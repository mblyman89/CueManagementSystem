"""
End-to-end handshake dry run.

Drives the EXACT controller handshake control flow (copied verbatim from
controllers/system_mode_controller.py::handle_execute_show_button) against the
REAL Pi execute_show.py (run as a local subprocess with mocked RPi.GPIO via
FakeSSHClient).

This proves the laptop controller logic and the Pi script speak the same
protocol end-to-end:
  1. file existence check          -> 'exists'
  2. clock offset probe (--now)    -> {"status":"time","pi_time":...}
  3. handshake launch (--handshake)-> Pi loads show + sets up GPIO
  4. Pi emits {"status":"ready"}    (flushed over pipe)
  5. laptop computes go_time, sends pi_go_time over STDIN
  6. Pi waits, emits {"status":"started"} then {"status":"success"}

The controller code constants used here MUST match the real ones:
  HANDSHAKE_READY_TIMEOUT = 20.0
  GO_LEAD_SECONDS         = 3.0  (we shrink to 1.0 for a fast test)
  OFFSET_PROBES           = 7
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fake_ssh import FakeSSHClient  # noqa: E402

# Match the real controller constants (GO_LEAD shortened so the test is quick).
HANDSHAKE_READY_TIMEOUT = 20.0
GO_LEAD_SECONDS = 1.0
OFFSET_PROBES = 7

SHOW_FILE = os.path.join(HERE, "sample_show.json")
LOG_FILE = "/tmp/e2e_show_execution.log"

results = {"passed": [], "failed": []}


def check(name, cond, detail=""):
    if cond:
        results["passed"].append(name)
        print(f"  [PASS] {name} {detail}")
    else:
        results["failed"].append(name)
        print(f"  [FAIL] {name} {detail}")


def measure_clock_offset(ssh):
    """Verbatim port of controller.measure_clock_offset."""
    offsets = []
    for _ in range(OFFSET_PROBES):
        try:
            t1 = time.time()
            stdin, stdout, stderr = ssh.exec_command("python3 ~/execute_show.py --now", timeout=5)
            line = stdout.readline().strip()
            t2 = time.time()
            data = json.loads(line)
            pi_time = float(data.get("pi_time"))
            offset = pi_time - (t1 + t2) / 2.0
            offsets.append(offset)
        except Exception as e:
            print(f"    probe failed: {e}")
            continue
    if not offsets:
        return 0.0
    offsets.sort()
    return offsets[len(offsets) // 2]


def run():
    print("=" * 70)
    print("END-TO-END HANDSHAKE DRY RUN (controller logic <-> real Pi script)")
    print("=" * 70)

    ssh = FakeSSHClient(SHOW_FILE, LOG_FILE)

    # --- Step 1: transport health (mirrors _get_or_create_ssh reuse check) ---
    check("transport is_active", ssh.get_transport().is_active())

    # --- Step 2: verify show file exists on Pi ---
    _in, _out, _err = ssh.exec_command("test -f /tmp/show_data.json && echo 'exists'")
    file_check = _out.read().strip()
    check("show file existence check", file_check == "exists", f"(got '{file_check}')")

    # --- Step 3: measure clock offset ---
    offset = measure_clock_offset(ssh)
    check("clock offset measured", offset is not None, f"(offset={offset * 1000:.2f} ms)")
    # Local subprocesses share the wall clock, so offset must be tiny.
    check("clock offset is small (local)", abs(offset) < 0.5, f"(|offset|={abs(offset) * 1000:.2f} ms)")

    # --- Step 4: launch handshake mode ---
    command = "python3 ~/execute_show.py /tmp/show_data.json --handshake 2>/tmp/e2e_show_execution.log"
    stdin, stdout, stderr = ssh.exec_command(command)
    channel = stdout.channel

    # --- Step 5: wait for READY (verbatim poll loop) ---
    start_wait = time.time()
    ready_received = False
    while time.time() - start_wait < HANDSHAKE_READY_TIMEOUT:
        if channel.recv_ready():
            line = stdout.readline().strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            status = data.get("status")
            if status == "ready":
                ready_received = True
                break
            if status == "error":
                check("Pi did not error before ready", False, f"({data.get('message')})")
                return
        else:
            time.sleep(0.005)
    check("Pi signaled READY within timeout", ready_received,
          f"(waited {time.time() - start_wait:.2f}s)")
    if not ready_received:
        try:
            with open(LOG_FILE) as f:
                print("    Pi log tail:\n" + f.read())
        except Exception:
            pass
        return

    # --- Step 6: compute go_time and send over STDIN (the channel Pi reads) ---
    laptop_go_time = time.time() + GO_LEAD_SECONDS
    pi_go_time = laptop_go_time + offset
    stdin.write(f"{pi_go_time}\n")
    stdin.flush()
    print(f"    sent pi_go_time={pi_go_time:.4f} (lead={GO_LEAD_SECONDS}s)")

    # --- Step 7: consume the Pi's started + success stream ---
    started = None
    success = None
    deadline = time.time() + GO_LEAD_SECONDS + 15.0
    while time.time() < deadline:
        line = stdout.readline()
        if line == "":  # EOF
            break
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except Exception:
            continue
        st = data.get("status")
        if st == "started":
            started = data
            print(f"    Pi started at pi_time={data.get('pi_time')}")
        elif st == "success":
            success = data
            print(f"    Pi success: {json.dumps(data)}")
            break
        elif st == "error":
            check("no error during run", False, f"({data.get('message')})")
            break

    check("Pi emitted 'started'", started is not None)
    check("Pi emitted 'success'", success is not None)

    if started is not None:
        # Verify the Pi actually waited for (didn't fire before) the go_time.
        pi_started_at = float(started.get("pi_time", 0))
        # started should be >= pi_go_time (within a small slack)
        check("Pi honored go_time (started >= go)",
              pi_started_at >= pi_go_time - 0.05,
              f"(started={pi_started_at:.4f} go={pi_go_time:.4f})")
        # And it should NOT have started absurdly late.
        check("Pi started near go_time",
              pi_started_at < pi_go_time + 0.5,
              f"(delta={(pi_started_at - pi_go_time) * 1000:.1f} ms)")

    if success is not None:
        # The sample show has 3 cues; confirm the count.
        # Real script nests it: success["timing_stats"]["total_cues"].
        stats = success.get("timing_stats", {})
        cues = stats.get("total_cues")
        check("all cues executed", cues == 3, f"(total_cues={cues})")
        # Sync error should be tiny on a local run.
        avg_err = stats.get("average_error_ms")
        if avg_err is not None:
            check("timing avg error is small", avg_err < 50.0, f"(avg_error_ms={avg_err})")


def main():
    try:
        run()
    finally:
        print("=" * 70)
        print(f"PASSED: {len(results['passed'])}   FAILED: {len(results['failed'])}")
        if results["failed"]:
            print("FAILED TESTS:")
            for f in results["failed"]:
                print(f"  - {f}")
        print("=" * 70)
    sys.exit(1 if results["failed"] else 0)


if __name__ == "__main__":
    main()
