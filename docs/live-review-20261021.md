# Live scan and architecture review - 21 October 2026

Scope: repeat the live/offline/browser/security/package investigation and record
bugs and improvements. No application fixes, dependency upgrades, normal-server
restart, commits, pushes or broad unused-code deletion in this review. Keep FastAPI,
local JSON, scope checks, instance ownership and original evidence intact.

Status: review completed. Four issues are recorded below, not implemented. The
existing regression/security gates passed, but the Light scan did not complete.

## Scope and deployment

Read-only preflight confirmed the previously authorised home range
`192.168.0.0/24`, this PC `192.168.0.216`, bound interface `eth6`, and the recorded
default-route connection before scanning. Both jobs use a separately owned current
backend and new `.test-artifacts/live-review-20261021/data/` folder. Pi-hole is
disabled. No normal session/household labels were imported or modified.

Current source build is `9337b5f1a4d8df457b11`, API contract 3. The normal backend
still runs build `3e5d3881e53f804e688b`, contract 2. The helper correctly reports
`source_match: false`, `restart_required: true`, despite matching static assets.
Finish active work and restart the normal backend task before claiming those fixes
are deployed. This review does not stop the user's process to make that check pass.

## Live observations

The Light job was accepted but a network-guard read could not verify the bound
interface during discovery. It finished as **failed**, with `NETWORK_INTERRUPTED`, reason
`interface_unavailable`; discovery never completed, no device service checks ran,
and no devices/findings were saved. The report overview still received local AI
wording. This is not an empty successful scan or proof that no devices are present.
No bypass, automatic repeat or extra target retry was submitted. A retained partial
`discovery.xml` proves Nmap discovery started; the ledger's `not_run` targets are
not proof that the discovery process itself never launched.

Three subsequent read-only Nmap interface-list queries returned the same `eth6`/
PC address as ready, in 0.600-0.761 seconds. That does not prove the cause of the
earlier failure. The saved diagnostic cannot distinguish an unavailable list,
unmatched range or ambiguity because the snapshot wrapper collapses these reasons.
Do not assert that Wi-Fi changed, Nmap timed out, or a particular device failed.

Deep completed **1/1** selected device check, with **14 open features** and five
review items: one low priority and four informational. It took 542 seconds from
saved start to finish (548.7 seconds observed by the browser helper, including
request/navigation overhead). There were no recorded check errors. The one warning
correctly qualifies a self-scan: this does not establish what another device or the
internet can reach. This PC's reverse-DNS name returned in 128 ms.

Compared offline with 20 October's saved Deep report, TCP 2869 was newly observed
open and identified as Microsoft HTTPAPI HTTP. That accounts for the additional
low HTTP review item. None of the previously open features disappeared. This is an
observed difference, not a newly confirmed vulnerability, an intruder, a verified
administration page or proof of remote exposure. No additional device/CVE queries
were made to investigate the difference.

Raw evidence replay reproduced all **21** Deep saved service records and all five
deterministic findings, with no missing completed-host XML. Light's 517-byte partial
discovery XML has a start header but no final run statistics/closing element; it
cannot establish completed discovery or an empty network. There is no completed
Light device/service evidence to replay and no naming-quality conclusion to draw
from that interrupted run.

Local Ollama produced one ready overview for failed Light and six ready records for
Deep (five items plus overview). All **seven** revalidated, with zero rejected fields
and no fixed-wording fallbacks in this pair. Selected structured inputs contained
no recorded addresses/MACs/hostnames or raw XML. This is validation of permitted
wording against saved facts, not proof of universal comprehension or unrestricted
AI-generated prose.

Exactly two scan submissions occurred; refresh retained both original jobs, and
both reports opened automatically after analysis. There were zero browser page
errors and no whole-page overflow at 320/390/768/1440 px. Exports, inventory filters/
reset and exact report-return context passed. The isolated inventory correctly
contains only the one checked PC, not an asserted list of every connected device.

All **853** protected normal report/evidence files remained unchanged. A **267-file**
app/test/script/lock/workflow manifest also stayed unchanged. The owned backend
closed after both jobs finished; independent checks found its wrapper PID 32624
and server PID 20148 absent and port 30668 without listeners. Normal backend/session
ownership was untouched. Its one recorded traceback is the known Light
`NetworkInterrupted` path, not an unrelated crash/unretrieved task. No blanket clean
live-scan pass is claimed.

### Beginner-reading and UI walkthrough

The failed Light report prominently says **Could not complete**, describes network
verification failure and retains **Run again**; it does not announce a clean bill
of health. However, its secondary unanswered-search sentence and **0 of 0** counter
need the distinction in F4. It also renders empty device/review search filters and
checklist content, making a failure report unnecessarily long on mobile.

Deep uses everyday feature examples, a clear self-scan caution, and adjacent warnings
not to enter passwords on HTTP pages or ignore certificate warnings. Its first
action is short and the details remain optional. Visual checks at 390 px found
readable wrapping and reachable controls. This is an assistant walkthrough and
automated geometry check, not a novice, screen-reader or physical-phone study.

## Reproduced issues, recommended execution order

### F1. Medium: a stale POST reply can overwrite a newer start intention

`app/static/js/dashboard.js` checks the operation ID before accepting recovery GETs,
but the original start POST's success/catch branches are not similarly correlated.
During slow preparation, **Return to scan setup** is visible. After its explicit
warning, a user may choose a separate new start. A late reply from the first attempt
then clears the second pending key and either attaches the earlier scan or enables
Scan again when the old attempt is rejected. These are two explicit intentions,
not an automatically duplicated backend job; the defect is incorrect UI ownership.

The synthetic probe reproduced both late-success and late-409 paths with the
actual page code. No HTTP/scanner/provider work was executed. The backend receipts
still distinguish intentions; this does not invalidate their at-most-one admission.

Fix/acceptance: correlate every POST completion/error/finalizer with its operation
and current UI generation. An abandoned/superseded attempt must not clear, enable,
redirect or replace a newer attempt. Keep its saved receipt/history accessible.
Test reset/new start with old success, 4xx, 5xx and lost response in both orders;
the newer URL/key/disabled state must remain unchanged. Do not cancel an earlier
accepted job merely because the user returned to setup.

### F2. Medium: pending-start recovery disappears when status fails

With an explicit `#start=<UUID>`, `loadStatus()` reads `/api/status` before restoring
the visible recovery controls. A status error leaves Scan disabled and both recovery
buttons hidden, without even attempting the original authenticated receipt read.
The error text remains, but the user loses the contextual retry route until a
reload/status success. The synthetic probe reproduced this with a 503 status reply.

Fix/acceptance: restore pending-start UI before readiness checks and keep an explicit
read-only recovery action available independently of scanner/AI readiness. Distinguish
an expired session from a transient status outage. Test status failure with readable
receipt/progress, then recovery; never POST another start or attach an arbitrary job.

### F3. Medium: interface-query diagnostics lose the actual reason

`app/scanner/network.py::connection_snapshot()` turns every no-address result from
`nmap_interface_diagnostic()` into `interface_unavailable`. Three synthetic cases
confirmed `list_unavailable`, `scope_unmatched` and `multiple_matches` all lose their
distinction. The live Light failure contains that generic reason, so its underlying
cause cannot now be recovered from the report. Later successful reads do not prove
what happened at the failed read.

Fix/acceptance: preserve a bounded structured reason through the guard and saved
error; distinguish timeout/process failure from actual missing/ambiguous interface
and observed network change. Consider sharing overlapping **fresh** local Nmap list
queries as Windows connection reads already do. If a local read is retried, no
scanner traffic may proceed while verification is unknown; never authorise from a
stale successful snapshot, broaden scope, or ignore a confirmed change. Test transient
read failures, multiple interfaces, real changes, concurrent jobs and query deadlines.

### F4. Low: failed discovery is described as devices not answering

`coverageSummary()` says **No devices answered the search for devices** whenever a
finished discovery-mode scan has zero discovered devices. In this actual Light
report, discovery is incomplete and every target is `not_run` with zero service-check
attempts; partial raw discovery output was retained.
The failed headline/caution are retained, but this secondary sentence incorrectly
suggests a completed unanswered search. A direct saved-data probe reproduced it.

Fix/acceptance: distinguish an unperformed/interrupted device search from a completed
search with no replies. Use a short sentence such as **The device search did not
finish, so no devices could be checked**. Test failed-before-discovery, interrupted
discovery, completed-empty discovery and partial completed checks. Preserve counts,
the failure explanation and the no-security-verdict limitation.

Observed-behaviour probes: private `probes/stale-start.mjs` covers late success,
late rejection, hidden recovery and this live coverage sentence; three parameterised
Python cases in `probes/test_guard_diagnostic.py` cover lost reasons. Their passes
mean the issues were reproduced, not fixed. No source regression was weakened.

## Improvements after fixes

1. Extract a small scan-start UI controller/state transition module, with one current
   operation/generation. Test late outcomes centrally instead of adding disconnected
   booleans and duplicate cleanup branches. Keep normal parallel scans independent.
2. Measure local interface-query count/latency under concurrent scans before changing
   deadlines. Prefer fresh single-flight reads and accurate diagnostics over more
   frequent processes or stale network authorisation. No guard bypass is recommended.
3. Design durable receipt maintenance before the 1 MiB/1,024-record limit becomes a
   usability problem. No silent eviction: expiring/deleting a receipt must not make
   an old intention eligible to execute again. Retain report reads under capacity.
4. Prioritise the prepared novice/disabled-reader and actual assistive-technology
   study. Include the failed-search distinction and unknown-start controls. Automated
   DOM/viewport checks do not establish comprehension or spoken output. Do not add
   more visible controls merely to make the report look more sophisticated.
5. Simplify failed/zero-evidence reports to the cause, what was not checked and one
   clear next action; avoid empty search/sort/checklist controls. Keep the original
   evidence, export and optional technical notes accessible. When discovery is
   incomplete, explain that instead of presenting **0 of 0** as useful coverage.
6. Restart/recheck the normal process when idle, then publish through the full hosted
   platform/browser matrix only when requested. Do not weaken local Windows WebKit
   security or upload private household reports/session logs as CI evidence.

## Completed independent gates

- Offline `.test-artifacts/checks-3923f38bab/`: full gate passed; 968 Python,
  277 JavaScript, 29 syntax checks, lint/202-file formatting. Five Windows link-
  privilege skips, 153 opt-in cases deselected.
- Actual Chromium/Firefox `.test-artifacts/review-browser-20261021.xml`:
  16 passed, zero failures/errors/skips; synthetic start recovery, exact/related
  CVE lookup/lost response, library and response-policy coverage. This is not a
  full hosted matrix or extra live network traffic.
- Security `.test-artifacts/security-f4b8c49ac5/`: both complete dependency graphs
  have no known vulnerabilities, 16 low static alerts retained, no medium/high
  static alerts and no potential secrets. No advisories were ignored.
- Installed wheel `.test-artifacts/package-2edb6e87ed/`: fresh build/runtime trust
  bootstrap and offline dependency consistency passed; seven pages, 31 static assets,
  synthetic report create/reopen/delete/Undo passed.
- All three existing project environments passed `pip check`. The separate Windows
  loopback-only diagnostic passed 20 concurrent synthetic subprocesses, 11 orderly
  and ten abrupt disconnects, zero diagnostic events. This is not the full app or
  proof that every possible Windows connection-reset scenario is resolved.

Live UI/raw/AI results are under `.test-artifacts/live-review-20261021/`, including
`evidence-audit.json`, `browser-results.json`, `integrity.json`, source manifest and
independent `cleanup-verification.json`. These artifacts contain private network
evidence; do not upload them as ordinary public CI/dissertation attachments.

## Code organisation and next execution

No confirmed unused application module required deletion in this pass. The API
compatibility routes, guard checks, evidence/annotation split, package assets and
recovery helpers have active purposes. Lint/import checks and the installed asset
check passed. A small tested start-controller extraction is preferable to unrelated
file moves while F1/F2 remain open. There is no evidence here requiring Flask,
SQLite, Pi-hole deployment or a different scanner to resolve these defects.

Recommended implementation: F1 stale-outcome ownership, F2 status-independent
recovery, F3 diagnostic preservation/fresh-query reliability, F4 interrupted-search
wording, then the failure-screen simplification and durable receipt-maintenance
design. Add focused acceptance tests rather than treating the reproductions as
fixes; run the offline/browser/security/package gates again, then a new bounded
authorised live pair when requested. Do not silently retry the interrupted Light
scan or mark its checks complete.

The probes and live failure are separate evidence from the passing existing suite.
No fix, new hosted run, participant, real AT or Ubuntu reference-lab result is claimed.
