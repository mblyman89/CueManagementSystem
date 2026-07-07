# CuePiShifter — Detailed Task List (Handoff Ready)

Legend: [ ] todo · [x] done · (P) Pi side · (L) Laptop side

## Phase 0 — Safety & Baseline
- [ ] Clone repo fresh into /workspace/repo
- [ ] Create branch `fix/show-execution-handshake`
- [ ] Re-read exact show call chain (main_window → system_mode_controller → execute_show)
- [ ] Record the current (broken) protocol in AUDIT_REPORT.md

## Phase 1 — Pi Side: execute_show.py (P)
- [ ] Add `--now` mode: print current Pi epoch time as JSON and exit (for clock-offset probe)
- [ ] Add `--handshake` mode flag parsing
- [ ] Load show file BEFORE signaling ready (fail fast if missing/invalid)
- [ ] Call setup_gpio() BEFORE signaling ready
- [ ] Print `{"status":"ready"}` then `sys.stdout.flush()`
- [ ] Read GO timestamp from stdin (float, Pi-clock epoch seconds)
- [ ] Validate stdin timestamp; error JSON + flush if bad
- [ ] Precise wait: sleep to T-2ms, spin to T
- [ ] Keep backward-compatible argv timestamp path
- [ ] Flush every stdout JSON emission
- [ ] Print `{"status":"started","pi_time":...}` right before firing (flushed)
- [ ] Keep final result JSON `{"status":"success",...}` at end (flushed)

## Phase 2 — Laptop Side: system_mode_controller.py (L)
- [ ] Add `measure_clock_offset(ssh)` — N probes via `--now`, return median offset
- [ ] Add constants: HANDSHAKE_READY_TIMEOUT=20, GO_LEAD_SECONDS=3.0, OFFSET_PROBES=7
- [ ] Rewrite `handle_execute_show_button()`:
  - [ ] Remove parallel local `execute_show()` call in hardware mode
  - [ ] Ensure single reused SSH connection (consistent 15s connect timeout)
  - [ ] Verify /tmp/show_data.json exists (keep existing check)
  - [ ] Measure clock offset once (cache on self)
  - [ ] Launch `execute_show.py <file> --handshake` (stderr tee'd, not hidden)
  - [ ] Real-time READY read using channel recv with select/timeout
  - [ ] On READY: compute laptop go_time = now + GO_LEAD_SECONDS
  - [ ] Convert to Pi clock: pi_go = go_time + offset
  - [ ] Send `pi_go` over stdin + flush
  - [ ] Return go_time (laptop clock) to caller via signal/attribute
  - [ ] Robust error emits on every failure branch
- [ ] Add `self.last_go_time` attribute for main_window to read
- [ ] Add `show_go_time_ready = Signal(float)` to emit the laptop go_time

## Phase 3 — Laptop Side: main_window.py (L)
- [ ] Stop computing an independent 500ms start_timestamp for music
- [ ] Connect to `show_go_time_ready` signal; start music at that laptop go_time
- [ ] Remove the local spin-wait race (or gate it behind simulation mode)
- [ ] Keep ABORT/button enable/disable logic intact
- [ ] Pass show_cues + no timestamp (controller decides timing now)

## Phase 4 — Reliability & Guardrails
- [ ] READY timeout success-fast behavior verified
- [ ] Pi stderr visible to laptop (tee to log AND read tail on failure) 
- [ ] Clear UI error messages for: file missing, ready timeout, stdin send fail, ssh drop
- [ ] Ensure ABORT still kills execute_show.py on Pi (pkill already present)

## Phase 5 — Verification
- [ ] `python -m py_compile` on all changed Python files
- [ ] Local mock-SSH dry run proving handshake control flow
- [ ] Produce on-hardware TEST_CHECKLIST.md steps
- [ ] Commit, push branch, open PR with summary

## Deployment Reminder (must-do on the night)
- [ ] Re-upload the updated `execute_show.py` to the Pi (Pre-Show Checklist upload, or scp)
- [ ] Confirm Pi has the new script: `md5sum ~/execute_show.py`
