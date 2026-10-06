# Live scans, architecture and cleanup review — 6 October 2026

Review only: fixes and removals below are not implemented. Application source,
normal report history and the existing backend were preserved. The isolated test
backend has been stopped. These results verify current source, not the already
running normal instance's loaded code.

## Live verification

Windows again showed WiFi `192.168.0.216/24`, gateway `192.168.0.1`. The authorised
Light target was `192.168.0.0/24`; Deep targeted this Windows computer only. Nmap
7.991, local Ollama `llama3.2:3b` and JSON storage passed preflight. Both jobs were
submitted through the real browser to an owned loopback backend on port 8766.
The preceding isolated live reports were copied into the new test folder to
exercise comparison history; normal history was not copied or modified.

| Result | Light | Deep — this PC |
| --- | ---: | ---: |
| Scan ID | `767dd883-f6a2-4752-a24a-e2b99a3e7626` | `8226e4d9-26a6-4a36-a2d0-36666c94077b` |
| Time including waiting and AI | 344.5 seconds | 592.3 seconds |
| Device checks finished | 11 of 11 discovered | 1 of 1 selected |
| Open services | 12 | 13 |
| Review items | 8: four low, four informational | 4 informational |
| Scan errors | 0 | 0 |
| Accepted AI records, including overview | 9 | 5 |

Deep's one note correctly discloses that checking this computer locally does not
establish which services another device can reach. Light had no warnings. There
were no unfinished device checks or backend exception tracebacks. The intermittent
Windows socket-reset issue remains open despite not recurring in this run.

Saved XML replay matched all 165 Light / 20 Deep service-state records and all
8 / 4 findings. All 14 ready AI records revalidated with zero rejected fields or
fallback records. Selected AI inputs contained no device IP, MAC, hostname or raw
XML. Light retained two current mDNS names; Deep retained a reverse-DNS name.
Names remain claims, not verified device identities.

Refresh during work, history reopening, Run again setup, four widths
(320/390/768/1440 px) and page-error checks passed for both profiles. Only two
network scans were submitted. Deep's Running indicator and stage tracker were
checked during the live device check. Light showed six available service
comparisons and five unreliable/unavailable comparisons; Deep had no reliable
comparison. These limits were disclosed, not labelled unchanged or safe.

The previous repeat observed six Light devices and 15 Deep open services. The
new counts differ; their causes were not established. A count change alone does
not prove a regression, intrusion, repair or that an absent device has gone away.

Artifacts: `.test-artifacts/review-live-20261006/` contains reports, XML, timelines,
screenshots, browser results, evidence replay and integrity checks. Original normal
reports and the copied historical reports were byte-for-byte unchanged. Diagnostic
checklist writes affected only the new isolated report, were reset to To check,
and did not change its scan evidence. Pi-hole and real external CVE lookups were
not exercised. Name/CVE responses used in the snapshot probe were intercepted.

## Confirmed findings and recommended execution order

### 1. Annotation snapshot adoption leaves checklist controls stale — priority P2

Location: `app/static/js/scan.js`, `cvePanel()` and the later-name lookup callback.
Both adopt a complete newer `annotations` snapshot, but do not synchronise visible
checklist controls. The CVE callback updates the report title only; name lookup
rerenders device summaries only.

Reproduction on the new Light report: save Checked through another client, deliver
the latest notes through an intercepted name/CVE response, then inspect the first
tab. Its control still shows To check although the saved status is Checked. Its
next edit is accepted using the newer revision, so the user can overwrite a review
they were never shown. Both callback paths reproduced this. Ordinary stale-revision
protection works; this is a UI snapshot-consistency gap, not a change to scan facts.

Next implementation: centralise full snapshot application. Apply revision, title,
checklists, later-name information, CVE notes and recovery notices together. Preserve
selected finding, filters, expanded cards and keyboard focus. Add two-tab browser
regressions combining checklist edits with name, CVE and title updates. Never adopt
a new revision alongside visibly stale editable fields.

Evidence: `snapshot-review.json`.

### 2. Storage error responses are inconsistent — priority P2

Location: `app/api/library.py`, annotations GET and report-title PUT.
Isolated fault injection produced:

- Unreadable annotation state: GET annotations returned generic HTTP 500.
- Disk-write `OSError`: title PUT returned generic HTTP 500.
- The same write error through checklist PUT returned the intended HTTP 503.

Global permission and lock handlers cover some failures, not all disk/read errors.
The factual scan remained unchanged; the report's fallback keeps evidence visible.

Next implementation: map unreadable/corrupt notes and failed writes to consistent,
plain-language responses without echoing paths or exception details. Preserve the
validated-backup recovery policy and revision checks. Cover read errors, invalid
primary/backup, full disk, failed atomic replacement and successful subsequent retry.
Do not silently reset annotations or retry a write against a new revision.

Evidence: `code-audit.json`, `annotation_error_paths`.

### 3. Checklist labels do not distinguish unnamed devices — priority P2 usability

Location: `app/static/js/scan.js`, `actionChecklist()`.
Its label uses `deviceLabel()` without the address or recorded role. The Light
report had three identical HTTP checklist labels and three identical RTSP labels
for different unnamed devices. The grouped Applies to paragraph lists addresses,
but does not connect each duplicate control to its corresponding device.

Next implementation: use a unique readable label for each control, including the
nickname/name and address, with recorded gateway/computer context where useful.
Do not expose internal UUIDs or invent identity. Test unnamed, duplicate-name and
renamed devices, screen-reader labels and mobile reflow. Prefer the reviewed plain
action text so the checklist does not repeat a more technical original instruction.

Evidence: `snapshot-review.json`, `duplicate_checklist_labels`.

### 4. Saved-report AI retries have no admission-count bound — architecture gap

Location: `app/jobs/supervisor.py`, `active_scan_count`, `has_capacity()` and
`request_explanations()`.
A synthetic probe with a blocked fake explanation service admitted six different
saved-report retries with capacity configured to five. `active_scan_ids` contained
six, while `active_scan_count` was zero and `has_capacity()` returned true. No real
scanner or model was called by this probe. Normal network-scan admission remains
bounded; serial AI execution and queue-time limits still apply.

Next implementation: make the admission policy explicit for network jobs and saved
AI retries. Bound the backlog and report queue counts consistently; account for an
existing scan's automatic AI phase without double-counting or denying that phase.
Use inline waiting feedback, not a capacity popup or automatic scan resubmission.
Test cancellation, queue expiry and capacity release after failures.

Evidence: `ai-queue-review.json`. This did not cause either live scan to fail.

### 5. Previously recorded Windows socket reset — unresolved dependency follow-up

No recurrence or new tracebacks were observed. Retain scoped diagnostics and the
saved evidence. Seek a reproducible supported-runtime remedy before changing the
runtime; do not suppress callbacks or mark it fixed because a run was clean.

## Code use and organisation

- Static import traversal reached all **65 application Python modules**. Routed
  template/static-asset tests passed: all five templates and nine JavaScript modules
  remain reachable. No unused application HTML/JS/Python file was identified.
- Apparent unreferenced subprocess and mDNS methods are framework callbacks and
  must stay. `storage_usage` is imported under an alias and used by its API route.
  The deferred Pi-hole connector remains an optional supported path, not an orphan.
- One small unused CSS candidate is `.action-check .text-button` in `app.css`: the
  checklist creates a label, select and feedback, not a nested text-button.
- Cleanup preview identified regenerated `build/` and `.ruff_cache/`: two folders,
  92 files. They can be archived then removed using the existing cleanup helper.
  Preview only was run. Package metadata/environments, IDE files, `.preview-data`,
  saved reports, evidence and historical documents were not selected for deletion.
- The main organisation opportunity is splitting annotation state/control updates
  from the large `scan.js` renderer. Solve the snapshot bug first, then extract the
  tested shared helper; avoid a broad rewrite that mixes mutable notes with evidence.

## Further improvements for nontechnical readers

1. Explain the remaining raw Deep service labels such as `msrpc` and `netbios-ssn`
   with reviewed plain-language text. Keep technical names/provenance in details;
   do not infer a vulnerability or exact product from a port label.
2. Use one consistent term for review items: the page still mixes findings, review
   items and informational. Explain that these are review priorities, not danger
   scores or proof of a break-in. No backend severity needs to change.
3. Explain recorded gateway role more simply, and make the local-self-check caution
   prominent. A local answer does not establish internet exposure or another
   device's access. Existing limitations must remain visible.
4. Show a specific reason when comparison is unavailable: first report, missing
   stable identity evidence, incompatible profiles or incomplete checks. Do not
   weaken identity rules to match solely by IP or claim a difference is a fix.
5. Add checklist-status filtering/progress, clearly labelled Your review progress,
   separate from scan coverage or security. New reports should not silently inherit
   Checked as proof that a new observation is safe.
6. Benchmark cold/warm history searches with larger synthetic JSON libraries before
   optimising them. Keep local JSON; no SQLite migration is needed for these fixes.
7. Conduct the planned nontechnical-reader study, real-phone accessibility checks
   and authorised Ubuntu evaluation. Browser emulation and accepted AI wording do
   not establish comprehension, all-phone compatibility or lab interoperability.

## Regression and limitations

Fresh full command: `.venv-quality/Scripts/python.exe -B scripts/check.py --browser
--browser-engines chromium,firefox,webkit`. **448 Python and 57 JavaScript tests
passed**, with one opt-in real-provider test deselected; lint/format and all nine
module syntax checks passed. Artifacts: `.test-artifacts/checks-550718e53f/`.
Actual Ollama was exercised separately by the live scans above.

The additional diagnostics found gaps not covered by that passing suite. No fixes
were implemented or source files removed during this review. The snapshot probe
initially used a locator whose button label changes and a dashboard that resumes
an active job; the corrected direct-report probe reproduced both defects without
extra scans or external lookups. Normal backend/history remain untouched.
