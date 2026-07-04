"""
Functional test of execute_show.py Pi-side modes using a mocked RPi.GPIO.

Proves:
  1. --now emits a time JSON and exits 0
  2. --handshake emits {"status":"ready"}, reads a GO timestamp from stdin,
     waits for it, emits started + success (all flushed)
  3. Legacy positional timestamp path still runs
"""
import subprocess
import sys
import os
import time
import json

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "repo")
SCRIPT = os.path.join(REPO, "CueManagementSystem", "raspberry_pi", "execute_show.py")
SHOW = os.path.join(HERE, "sample_show.json")
MOCK = os.path.join(HERE, "mock_RPi")

env = dict(os.environ)
# Put mock RPi on the path so `import RPi.GPIO` resolves to our stub
env["PYTHONPATH"] = MOCK + os.pathsep + env.get("PYTHONPATH", "")

# Make mock_RPi a package: RPi.GPIO
os.makedirs(os.path.join(MOCK, "RPi"), exist_ok=True)
open(os.path.join(MOCK, "RPi", "__init__.py"), "w").close()
# Move GPIO.py under RPi/
import shutil
if os.path.exists(os.path.join(MOCK, "GPIO.py")):
    shutil.move(os.path.join(MOCK, "GPIO.py"), os.path.join(MOCK, "RPi", "GPIO.py"))


def run(args, stdin_data=None, timeout=15):
    p = subprocess.Popen(
        [sys.executable, SCRIPT] + args,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, text=True,
    )
    out, err = p.communicate(input=stdin_data, timeout=timeout)
    return p.returncode, out, err


def parse_lines(out):
    objs = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            objs.append(json.loads(line))
        except Exception:
            pass
    return objs


print("=== TEST 1: --now clock probe ===")
rc, out, err = run(["--now"])
objs = parse_lines(out)
assert rc == 0, f"--now exit code {rc}, stderr={err}"
assert objs and objs[0].get("status") == "time", f"unexpected: {out}"
assert isinstance(objs[0].get("pi_time"), (int, float)), f"no pi_time: {out}"
print("  PASS: got", objs[0])

print("\n=== TEST 2: --handshake full flow ===")
# We send a GO timestamp ~1.0s in the future (Pi clock == our clock in this test)
go = time.time() + 1.0
t0 = time.time()
rc, out, err = run([SHOW, "--handshake"], stdin_data=f"{go}\n")
elapsed = time.time() - t0
objs = parse_lines(out)
statuses = [o.get("status") for o in objs]
print("  statuses:", statuses)
print("  stderr sync lines:")
for l in err.splitlines():
    if "[Sync]" in l:
        print("    ", l)
assert rc == 0, f"handshake exit {rc}, err={err}"
assert "ready" in statuses, f"no ready signal: {out}"
assert "started" in statuses, f"no started signal: {out}"
assert "success" in statuses, f"no success result: {out}"
# It must have actually waited (started at/after go time)
started_obj = next(o for o in objs if o.get("status") == "started")
assert started_obj["pi_time"] >= go - 0.05, f"started too early: {started_obj['pi_time']} vs go {go}"
print(f"  PASS: waited ~{elapsed:.2f}s, honored GO timestamp")

print("\n=== TEST 3: --handshake with invalid GO ===")
rc, out, err = run([SHOW, "--handshake"], stdin_data="not_a_number\n")
objs = parse_lines(out)
statuses = [o.get("status") for o in objs]
assert "ready" in statuses, f"no ready: {out}"
assert "error" in statuses, f"expected error for bad GO: {out}"
assert rc == 1, f"expected exit 1, got {rc}"
print("  PASS: invalid GO rejected cleanly ->", [o for o in objs if o.get('status')=='error'])

print("\n=== TEST 4: legacy positional timestamp path ===")
go = time.time() + 0.5
rc, out, err = run([SHOW, str(go)])
objs = parse_lines(out)
statuses = [o.get("status") for o in objs]
assert rc == 0, f"legacy exit {rc}, err={err}"
assert "started" in statuses and "success" in statuses, f"legacy failed: {out}"
# Legacy path must NOT emit a ready (no handshake)
assert "ready" not in statuses, f"legacy should not emit ready: {out}"
print("  PASS: legacy path runs and waits")

print("\n=== TEST 5: no-timestamp immediate run ===")
rc, out, err = run([SHOW])
objs = parse_lines(out)
statuses = [o.get("status") for o in objs]
assert rc == 0 and "success" in statuses, f"immediate run failed: {out}"
print("  PASS: immediate run works")

print("\nALL PI-SIDE TESTS PASSED")
