# CuePiShifter — On-Hardware Test Checklist (Night-Of)

Do these in order. Stop and note any failure. NO PYRO CONNECTED for steps 1–7.

## A. Pre-Flight (safety first)
- [ ] Igniters / e-matches DISCONNECTED from all outputs
- [ ] Pi powered, reachable (ping the Pi IP)
- [ ] Laptop connected to Pi (Ethernet static IP or WiFi adhoc "cuepishifter")

## B. Deploy Updated Pi Script
- [ ] Upload the new scripts (Pre-Show Checklist "upload" or scp)
- [ ] Verify on Pi: `ls -l ~/execute_show.py`
- [ ] Verify new modes exist: `python3 ~/execute_show.py --now` prints `{"status":"time","pi_time":...}`

## C. Connectivity Sanity
- [ ] App: Test Connection → success
- [ ] Fire a SINGLE CUE (dry) → outputs LED/relay clicks as expected (no pyro)
- [ ] Confirm single cue still works after the update (regression guard)

## D. Clock Offset Probe
- [ ] Start a show (dry). In logs, confirm: "Clock offset measured: X ms"
- [ ] Offset should be stable/reasonable (typically < a few hundred ms)

## E. Handshake Dry Run (NO PYRO)
- [ ] Start show. Logs show, in order:
  - [ ] "Launching execute_show.py --handshake"
  - [ ] "Received from Pi: {\"status\": \"ready\"}"
  - [ ] "Pi is READY"
  - [ ] "Sending GO (pi_time=...)"
  - [ ] "GO signal sent"
- [ ] Pi log (/tmp/show_execution.log) shows: waiting → started → success
- [ ] App reports show completed successfully (not "Pi did not signal ready")

## F. Music Sync Dry Run (NO PYRO)
- [ ] Select a music file, start show
- [ ] Music begins at the same moment the Pi reports "started"
- [ ] First cue timing lines up with the intended beat (watch LEDs/relays)

## G. ABORT Test (NO PYRO)
- [ ] Start show, press ABORT mid-run
- [ ] Pi process killed (app log: "Killed any running show processes")
- [ ] Outputs disabled + disarmed (get_gpio_status shows safe state)

## H. Live (PYRO CONNECTED) — only after A–G pass
- [ ] Arm system
- [ ] Enable outputs
- [ ] Execute show
- [ ] Confirm cues fire on time with music
- [ ] ABORT reachable at all times

## Notes
- If READY never arrives: confirm the Pi has the UPDATED execute_show.py (md5sum).
- If music is ahead/behind cues: check "Clock offset measured" value in logs.
- If show starts too early on Pi: increase GO_LEAD_SECONDS in system_mode_controller.py.
