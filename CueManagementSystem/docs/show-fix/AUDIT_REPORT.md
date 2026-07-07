# CuePiShifter — Revised Handshake & Network Audit Report

## Executive Summary

**Your problem is a software bug, not a cable issue.** The fact that single cues fire successfully over both the 100' Ethernet cable AND the WiFi adhoc network, while the full show fails on both, proves this conclusively. The physical network layer works fine — SSH connects, commands execute, individual cues fire. The failure is specific to the show execution code path.

The root cause is a **broken two-way handshake protocol** in `system_mode_controller.py` that was designed but never fully implemented on the Pi side. Combined with a timing race condition and the stdin/stdargv mismatch, the show execution path is fundamentally broken. It may have appeared to work with the 6' cable by accident (the Pi ran the show despite the handshake failure, not because of it succeeded).

---

## The Smoking Gun: Single Cue Works, Show Doesn't

### What happens during a single cue fire (✅ WORKS):

```
Laptop → SSH → Pi: python3 ~/execute_cue.py '{"type":"SINGLE SHOT","output":5,"duration":500}'
Pi → executes cue → prints {"status":"success"} to stdout
Laptop → reads stdout.channel.recv_exit_status() (BLOCKS until done)
Laptop → reads result → closes SSH
```

This is a simple **synchronous request-response**. The laptop blocks until the Pi finishes. No handshake, no stdin, no timing synchronization. It just works.

### What happens during a full show (❌ FAILS):

```
1. Laptop calculates: start_timestamp = time.time() + 0.5
2. Laptop → SSH → Pi: python3 ~/execute_show.py /tmp/show_data.json <start_timestamp> 2>/tmp/show_execution.log
3. Pi starts running. Reads start_timestamp from sys.argv[2].
4. Pi begins WAITING for the start_timestamp (spin-wait loop).
5. MEANWHILE on the laptop: enters READY-wait loop, polling stdout for {"status":"ready"}
6. Pi NEVER sends {"status":"ready"} — this signal doesn't exist in execute_show.py
7. Laptop spins for 10 seconds waiting for a signal that never comes
8. Laptop times out: ready_received = False → sets success = False
9. If the READY HAD been received, laptop would send final_timestamp via stdin...
   ...but Pi reads from sys.argv, not stdin, so the GO signal goes nowhere
10. Meanwhile, the Pi has been spin-waiting for the ORIGINAL start_timestamp from step 1
```

**Here's the critical race condition**: The `start_timestamp` is calculated at step 1 as `time.time() + 0.5` (500ms in the future). But by the time:
- The SSH command is sent (~100ms)
- The Pi process starts (~50-200ms)
- The Pi begins its spin-wait loop

...the start_timestamp may have **already passed**. The Pi's spin-wait code is:

```python
while time.time() < start_timestamp - 0.001:
    time.sleep(0.001)
while time.time() < start_timestamp:
    pass  # Busy-wait
```

If `start_timestamp` is already in the past when this code runs, the while-loop condition is immediately false, and the Pi **skips the wait entirely** and starts executing the show immediately. OR, there's a subtle problem: the laptop and Pi clocks may not agree on what time it is (no NTP over a direct connection), so the Pi might think the timestamp is in the future when the laptop thinks it's in the past, or vice versa.

But the bigger issue is: **what does the laptop do during those 10 seconds of READY-wait?** While it's polling stdout for a READY signal that never comes, the Pi may have already started and even FINISHED the show. The show's final result JSON (`{"status": "success", ...}`) gets printed to stdout, and the laptop's polling loop may try to parse it:

```python
data = json.loads(line)
if data.get('status') == 'ready':  # This will be "success", not "ready"
    ready_received = True
    break
```

Since `"success" != "ready"`, the laptop ignores the actual show result and keeps waiting. After 10 seconds, it gives up. The show on the Pi may have already completed, but the laptop reports failure.

**Why did it sometimes work with the 6' cable?** With a very fast connection, the timing might work out differently — the show could complete quickly, and the laptop's error handling might not cause visible problems. The user might see fireworks and think it worked, not realizing the handshake failed and the synchronization was off. Or the behavior may have been intermittent — sometimes the timing worked out, sometimes it didn't.

---

## Detailed Bug List (Prioritized)

### BUG #1: Pi Never Sends READY Signal (CRITICAL)

**File**: `execute_show.py` — `main()` function
**File**: `system_mode_controller.py` — `handle_execute_show_button()`, line ~942

The laptop polls for `{"status": "ready"}` on stdout. The Pi never outputs this. The only stdout output from `execute_show.py` is the final result JSON after the show completes.

### BUG #2: GO Timestamp Sent via stdin, Pi Reads from sys.argv (CRITICAL)

**File**: `system_mode_controller.py`, line ~976: `stdin.write(f"{final_timestamp}\n")`
**File**: `execute_show.py`, line ~357: `start_timestamp = float(sys.argv[2])`

The laptop sends the final timestamp through stdin, but the Pi reads the start timestamp from the command-line argument. These are two completely different input channels. The GO signal goes into a void.

### BUG #3: No stdout.flush() — Signal Would Be Buffered Anyway (CRITICAL)

Even if you added `print(json.dumps({"status": "ready"}))` to `execute_show.py`, it wouldn't reach the laptop. SSH `exec_command()` creates a pipe (not a terminal), so Python uses **block buffering** (typically 4KB or 8KB buffers). A short JSON line like `{"status":"ready"}` (20 bytes) would sit in the buffer and never be sent. You need `sys.stdout.flush()` after every stdout output that the laptop needs to see in real-time.

### BUG #4: 500ms Timestamp Is Too Tight (HIGH)

**File**: `main_window.py`, line ~713: `start_timestamp = time.time() + 0.5`

The show is launched with a start timestamp only 500ms in the future. But the sequence is:
1. Calculate timestamp (time X + 0.5s)
2. `asyncio.create_task(handle_execute_show_button(...))` — this schedules the coroutine but doesn't await it immediately
3. The laptop immediately starts its own spin-wait for the same timestamp
4. Meanwhile the async task needs to: establish SSH connection → send command → Pi starts process → Pi reads timestamp → Pi starts waiting

If the async task takes more than 500ms to get the Pi process started (very possible, especially over WiFi), the Pi receives a timestamp that's already in the past. The spin-wait skips, and the show starts immediately on the Pi while the laptop is still waiting to start music.

### BUG #5: No Clock Synchronization Between Laptop and Pi (HIGH)

**File**: `execute_show.py`, lines ~371-385; `main_window.py`, lines ~745-753

Both the laptop and Pi use `time.time()` to wait for the same `start_timestamp`. But `time.time()` returns the local wall clock, and over a direct Ethernet or WiFi connection with no internet, there's no NTP to keep the clocks synchronized. If the Pi's clock is even 500ms off from the laptop's, the synchronization is completely wrong — the Pi fires cues at the wrong time relative to the music.

### BUG #6: Laptop Does Local Show Execution AND Pi Show Execution (MEDIUM)

**File**: `system_mode_controller.py`, `handle_execute_show_button()`, line ~893

The code does this:
```python
if self.show_execution_manager.load_show(show_cues):
    success = await self.show_execution_manager.execute_show()
    # THEN if in hardware mode, also send to Pi...
```

It executes the show locally (in the ShowExecutionManager) AND sends it to the Pi. In hardware mode, the local execution is supposed to be skipped (the Pi handles it), but the code still calls `execute_show()` first. This may cause the laptop to start its own cue execution sequence while also trying to manage the Pi's execution.

### BUG #7: SSH Connection Inconsistency (MEDIUM)

Various methods use different SSH connection patterns:
- `_connect_via_ssh()`: 30-second timeout, stores connection in `self.ssh_connection`
- `handle_enable_outputs_button()`: 10-second timeout, creates fresh connection, never stores it
- `handle_execute_show_button()`: tries to reuse `self.ssh_connection`, falls back to fresh with 10-second timeout
- `handle_abort_button()`: creates fresh connection with 10-second timeout

None of these use the centralized `HardwareController` SSH management. The `HardwareController` class exists but is essentially unused — its methods reference scripts that don't exist in the repository.

### BUG #8: stderr Redirected Away (LOW)

**File**: `system_mode_controller.py`, line ~930: `2>/tmp/show_execution.log`

The Pi's stderr is redirected to a log file on the Pi. This means all the sync timing messages (`[Sync] Waiting for start timestamp`, `[Sync] Sync error: Xms`) are invisible to the laptop. If the show fails, there's no way to see what happened without SSHing into the Pi and reading `/tmp/show_execution.log`.

---

## Revised Diagnosis: Why the 100' Cable Appeared to Be the Problem

| Symptom | Actual Cause |
|---------|-------------|
| 100' cable "doesn't work" for shows | The show execution code path is broken — the handshake always fails |
| 6' cable "works" for shows | The show may have run despite the handshake failure (Pi ignores the broken GO signal and uses the original argv timestamp, which may have been close enough) |
| Single cue works on any cable | Single cue uses a completely different, simpler code path (synchronous SSH exec) that doesn't involve the broken handshake |
| WiFi adhoc also fails for shows | Confirms it's software, not cable — same broken handshake over a different physical layer |
| Pi 3B+ also has the same issue | Confirms it's not Pi hardware — the bug is in the Python code, not the platform |

**The 100' cable was a red herring.** You happened to test the show with the longer cable, and the show failed because of the software bugs. The short cable appeared to work because the timing happened to be close enough, or because the show ran despite the handshake failure and you saw fireworks firing (possibly at the wrong time or without music sync).

---

## Recommendations

All of these bugs need to be fixed, but the first three are show-stoppers that must be addressed before the system will work reliably.

See the separate ROADMAP.md for a phased implementation plan.
