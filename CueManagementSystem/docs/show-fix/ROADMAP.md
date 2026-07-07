# CuePiShifter — Show Execution Fix Roadmap

## Mission
Fix the broken show execution / handshake so that a full firework show launches reliably and stays synchronized with music, over any connection (Ethernet or WiFi adhoc). Single-cue firing already works; the show path must be brought to the same level of reliability.

## Root Cause (Confirmed)
The two-way handshake between the laptop and the Pi is broken:
- The Pi never emits the `{"status":"ready"}` signal the laptop waits for.
- The GO timestamp is sent by the laptop over **stdin**, but the Pi reads it from **sys.argv**.
- The Pi's stdout is block-buffered (SSH pipe), so even a correct READY signal would never flush.
- The 500 ms start window is too small to cover SSH + process launch, so the target time is frequently already in the past.
- Laptop and Pi clocks are never synchronized, so music-to-cue sync drifts.
- The laptop runs a local show sequence in parallel with the Pi's show.

## Design Decision: Robust One-Way Launch + Explicit READY Handshake
We will implement a clean, deterministic protocol:

1. Laptop opens (or reuses) one SSH connection.
2. Laptop launches `execute_show.py <file> --handshake` (no timestamp yet).
3. Pi loads the show, sets up GPIO, and prints `{"status":"ready"}` to stdout **with an explicit flush**.
4. Laptop reads the READY line (real-time, unbuffered channel read).
5. Laptop measures the clock offset between itself and the Pi (median of several probes) — done **once** before launch, cached.
6. Laptop computes `go_time = time.time() + LEAD_SECONDS` (generous, e.g. 3 s) and converts it to Pi clock time using the measured offset.
7. Laptop sends the Pi-clock GO timestamp over stdin; Pi reads stdin, waits until that Pi-clock time, then runs the show.
8. Laptop starts the music at its own `go_time` (its own clock), so music and cues line up.
9. Pi streams progress/among final result JSON back on stdout; laptop reads it without blocking the UI.

This removes every failure mode: READY is real and flushed, GO travels on the channel the Pi actually reads, the clock offset is corrected, and the lead time is generous.

## Phases

### Phase 0 — Safety & Baseline (no behavior change)
- Clone repo fresh, create working branch.
- Snapshot current behavior in notes.
- Confirm the exact call chain for show execution.

### Phase 1 — Pi Side: execute_show.py
- Add `--handshake` mode.
- Emit `{"status":"ready"}` + `sys.stdout.flush()` after load + GPIO setup.
- Read GO timestamp from **stdin** (Pi-clock seconds since epoch).
- Wait precisely (sleep + spin) for that Pi-clock time.
- Add a tiny time-echo mode (`--now`) so the laptop can measure clock offset.
- Keep backward-compatible argv timestamp path for safety.
- Flush all stdout JSON.

### Phase 2 — Laptop Side: system_mode_controller.py
- Add `measure_clock_offset()` (median of N probes using `--now`).
- Rewrite `handle_execute_show_button()`:
  - Launch with `--handshake`.
  - Real-time READY read on the paramiko channel (not `readline` polling that can miss).
  - Compute generous `go_time`; convert to Pi clock; send over stdin + flush.
  - Do NOT run the local show sequence in hardware mode.
  - Return the chosen `go_time` (laptop clock) so the UI can sync music to the same instant.
- Consistent SSH timeouts; reuse one connection.

### Phase 3 — Laptop Side: main_window.py
- Use the `go_time` returned by the controller to start music (no independent 500 ms guess).
- Increase lead time; remove the parallel local spin-wait that races the controller.
- Keep ABORT wired.

### Phase 4 — Reliability & Guardrails
- Increase READY timeout to a safe value (e.g. 20 s) but succeed the instant READY arrives.
- Surface Pi stderr (do not silently redirect to a file) OR tee it so failures are visible.
- Verify show file exists (already present) and validate JSON.
- Clear error messages to the UI on every failure branch.

### Phase 5 — Verification
- Static import/lint checks on changed files.
- Dry-run simulation of the handshake logic locally (mock SSH) to prove the control flow.
- Provide a manual on-hardware test checklist.

## Files To Change
- `raspberry_pi/execute_show.py` (Pi)
- `controllers/system_mode_controller.py` (laptop)
- `views/main_window.py` (laptop)
- (Docs) `RPi_network_setup.md` note about re-uploading the Pi script

## Non-Goals (tonight)
- Rewriting the whole networking stack.
- Switching transport (keep SSH; it works for single cues).
- Refactoring unrelated managers.

## Rollback
All work on a branch. If anything regresses, revert the branch. The backward-compatible argv path in `execute_show.py` means the Pi script still runs even if the laptop sends an old-style command.
