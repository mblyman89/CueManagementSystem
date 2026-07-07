"""
Prove the relative-GO design is immune to a wildly wrong Pi wall clock.

This reproduces the real-world failure: the Pi on a direct Ethernet link has no
NTP, so time.time() can be ~39 days off. We monkey-patch time.time() inside a
subprocess to return a badly wrong value, then confirm the Pi still:
  - emits READY
  - waits the correct RELATIVE delay (measured with perf_counter, unaffected)
  - fires all cues on time

If the Pi were still depending on wall-clock alignment, a 39-day offset would
break it. Because it uses a monotonic countdown, it must not care.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "repo")
SCRIPT = os.path.join(REPO, "CueManagementSystem", "raspberry_pi", "execute_show.py")
MOCK = os.path.join(HERE, "mock_RPi")
SHOW = os.path.join(HERE, "sample_show.json")

# A shim that skews time.time() by -39 days but leaves perf_counter() alone,
# then execs the real Pi script.
SHIM = r'''
import time as _t
_SKEW = -39 * 24 * 3600  # 39 days behind, like the real Pi
_orig = _t.time
_t.time = lambda: _orig() + _SKEW
import runpy, sys
sys.argv = [%r, %r, "--handshake"]
runpy.run_path(%r, run_name="__main__")
''' % (SCRIPT, SHOW, SCRIPT)

failed = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    if not cond:
        failed.append(name)


def main():
    print("=" * 70)
    print("WRONG-CLOCK IMMUNITY TEST (Pi wall clock skewed -39 days)")
    print("=" * 70)

    env = dict(os.environ)
    env["PYTHONPATH"] = MOCK + os.pathsep + env.get("PYTHONPATH", "")

    proc = subprocess.Popen(
        [sys.executable, "-c", SHIM],
        stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1, env=env,
    )

    # Read READY
    ready = False
    skewed_time = None
    for _ in range(50):
        line = proc.stdout.readline().strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except Exception:
            continue
        if data.get("status") == "ready":
            ready = True
            break
    check("Pi (wrong clock) signaled READY", ready)
    if not ready:
        print(proc.stderr.read())
        _finish()
        return

    # Send relative GO of 1.0s
    go_delay = 1.0
    t0 = time.time()
    proc.stdin.write(f"GO {go_delay}\n")
    proc.stdin.flush()

    started_at = None
    success = None
    while time.time() - t0 < 15:
        line = proc.stdout.readline()
        if line == "":
            break
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except Exception:
            continue
        if data.get("status") == "started":
            started_at = time.time()
            skewed_time = data.get("pi_time")
        elif data.get("status") == "success":
            success = data
            break

    check("Pi emitted 'started' despite wrong clock", started_at is not None)
    check("Pi emitted 'success' despite wrong clock", success is not None)

    if started_at is not None:
        elapsed = started_at - t0
        check("Relative delay honored (monotonic, offset-immune)",
              abs(elapsed - go_delay) < 0.5,
              f"(elapsed={elapsed:.3f}s target={go_delay}s)")

    if skewed_time is not None:
        # Confirm the Pi's reported wall clock really was skewed ~39 days,
        # proving the shim worked and yet timing still succeeded.
        days_off = (time.time() - skewed_time) / 86400.0
        check("Pi wall clock really was ~39 days off (shim active)",
              days_off > 35,
              f"(days_off={days_off:.1f})")

    if success is not None:
        cues = success.get("timing_stats", {}).get("total_cues")
        check("all cues executed", cues == 3, f"(total_cues={cues})")

    _finish()


def _finish():
    print("=" * 70)
    print(f"FAILED: {len(failed)}")
    for f in failed:
        print(f"  - {f}")
    print("=" * 70)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
