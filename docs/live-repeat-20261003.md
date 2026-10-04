# Task recovery and repeat live verification — 3 October 2026

## VS Code task recovery

The agent-owned background backend from the previous verification was still holding
port 8765 and the normal data-folder instance lock. Consequently the user's VS Code
Start backend task could not create another server. The verified idle process was
stopped; no saved scans were removed. The task terminal now reveals startup output
instead of hiding it. This was a handoff/process ownership error, not missing Nmap.

The requested repeat verification starts one temporary backend using the workspace
runtime. Its controller checks for active jobs before stopping only its own process
tree after verification. A live job must never be interrupted merely to free a port.

## Repeat verification

Preflight confirmed the authorised home subnet `192.168.0.0/24`, Nmap 7.991 and local
llama3.2:3b availability. No router settings were changed and no external home-device
fingerprint lookup was performed. Pi-hole remains deferred.

- Full isolated regression passed: 394 Python tests, 50 JavaScript tests, three
  browser engines, lint/format and JavaScript syntax. One real-provider test was
  deselected; the existing Starlette/httpx deprecation warning remains.
  Artifact: `.test-artifacts/checks-046c935987/`.
- Light `4059214c-ff2b-4aa2-bfe8-71d609dbe264` finished in 260.6 seconds, checking ten
  of 11 discovered devices. It saved 12 open services and eight review items.
  `.226` remained unreachable after two attempts; the cause was not established.
  The report explicitly says one device could not be checked. AI processing finished.
- Light refresh/history and 320/390/768/1440-pixel layout checks passed with no page
  errors. Discovery counts are observations at scan time, not a complete inventory.
- Deep `062d346e-10dc-47d9-b8d0-64c14a36a49a` targets only the Sony freshly identified
  by mDNS in this Light run. It completed on its first attempt in 610.9 seconds:
  15 open services, ten review items (two low, eight informational), no warnings
  or scan errors. All 11 AI records were accepted and revalidated.

Final evidence replay matched 150 Light service-state records/eight findings and
30 Deep service-state records/ten findings. Light used seven accepted AI records
and two reviewed fallbacks (`not_simpler`); no rejected fields were present.
Both selected AI inputs were free of device IPs, names, MAC addresses and raw XML.
Both reports passed refresh/history and all four viewport widths. Run again passed
for Light and both Deep target choices, with no extra scan submissions. All 155
pre-existing scan JSON files remained unchanged. Exactly two scans were submitted.

The controller verified idle state and stopped its own temporary backend, releasing
the task's port. At the 4 October follow-up, a different process was listening;
it matched the normal workspace `-m app serve --port 8765` command and was not
stopped. Real-reader, physical-device accessibility and Ubuntu evaluation
remain pending; external CVE lookup using home fingerprints was not performed.
Artifacts: `.test-artifacts/live-repeat-20261003/`.
