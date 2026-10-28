# Full verification and live scans - 27 October 2026

Status: verification complete; **not all gates passed**. This is a read/check
execution, not a new round of application changes. Findings and recommendations
are recorded separately below.
The [preceding implementation](fixes-cve-20261027.md) retains its original evidence.

## Scope and preservation

- Source build `1b6127342ba5b5601dc3`, API contract 3; local HEAD `a131355` with
  unpublished fixes and earlier documentation edits preserved. No commit/push,
  workflow rerun, deletion of application files or normal-backend restart here.
- Current default-route detection matched the previously authorised home scope.
  Light scans that home range; Deep targets only this Windows PC. Both run in the
  new isolated `.test-artifacts/live-review-20261027/data/` folder. Pi-hole is off.
  Neither another device nor another network is added to the authorised scope.
- Normal app public build/contract/served assets match current source. Existing
  reports, nicknames and settings are protected from destructive feature tests.
  Delete/Undo, storage failure, cancellation and settings cases use synthetic data.
- A 274-file app/test/script/workflow/lock hash manifest was taken before checks.
  Private device identifiers, model payloads, logs and screenshots stay in ignored
  test artifacts; they are not uploaded as public documentation.

## Verification results

- Offline `.test-artifacts/checks-fedd3a4c49/`: 1,000 Python passes, five Windows
  privilege skips, 165 opt-in deselections; 301 JavaScript passes, 30 syntax checks,
  lint/205-file formatting passed.
- Fresh security `.test-artifacts/security-947c61390f/`: both complete pinned
  dependency graphs have no known advisories; static analysis records 16 low,
  zero medium/high findings; secret detection records zero potential secrets.
- Fresh installed wheel `.test-artifacts/package-1124ad9342/`: seven pages,
  32 assets, synthetic create/reopen/delete/Undo and dependency consistency passed.
- Live Light: **partial**, two of six discovered devices checked, three answering
  features, two review items (one low, one informational). Four devices remained
  unfinished. Live Deep: **failed**, zero of one selected device checks completed,
  no usable service/finding result. Both saved `NETWORK_INTERRUPTED/list_timeout`.
  These are not two successful scan outcomes.
- The browser flow itself passed: exactly two submissions, both running jobs
  survived refresh, both reports opened after analysis, no page errors or horizontal
  overflow at 320/390/768/1440 px. Export previews, inventory views/reset/return,
  feature/comparison/support sections passed. Partial/failed evidence stayed readable.
  The helper's exit zero/`LIVE_SCAN_PAIR_COMPLETE` describes this flow; it is not
  a scan-coverage pass.
- Read-only raw replay reproduced all 30 service records and two deterministic
  findings from the completed Light checks. No raw evidence was missing for those
  checks. Four ready AI records revalidated (three Light, one failed-scan overview),
  with no rejected fields/fallback reasons and no private identifiers/raw XML in
  model input. Deep has no completed evidence to replay: zero is not a replay of
  a successful Deep scan. One optional certificate interpretation was absent
  because enrichment was interrupted; it is not a passed certificate check.
- A fresh actual NVD lookup on the saved lighttpd fingerprint examined 35 unique
  product records and returned five related cases prioritised by recorded dates.
  Exact-version references remained zero. Related research completed without a
  partial-search flag; Ollama returned validated reviewed context with no fallback.
  No report/annotation was changed and no additional device scan was started.
  This confirms provider operation, not applicability of those CVEs to the device.
- Complete Chromium suite `.test-artifacts/checks-0016d48270/`: **163 passes**,
  no browser skips/errors. Complete Firefox `.test-artifacts/checks-080fd3752c/`:
  **163 passes**, no browser skips/errors. Complete WebKit `.test-artifacts/checks-d6ac32e19f/`:
  **163 passes, one teardown error**, no skips; see F5. This is a failed gate.
  Browser checks are separate from actual scans and actual NVD/local-model checks.
- Windows loopback-only Proactor diagnostic passed 11 orderly/10 abrupt disconnects
  alongside 20 subprocesses, remaining responsive with zero recorded callbacks.
  This is not evidence that local adapter enumeration cannot time out.
- Normal/QA/security `pip check` passed. Read-only normal app readiness still
  confirms the current build, Nmap and Ollama ready, storage OK and zero active
  normal scans. All 853 existing evidence files stayed unchanged. The isolated
  backend's launcher/child processes are absent and its port is independently
  confirmed closed; the normal backend was left running.

## Hosted CI

Read-only GitHub inspection reconfirmed that
[run 24](https://github.com/YoanKirilov/MSc-Major-Project/actions/runs/39670678601)
still has 15 successful jobs and two failed Windows WebKit jobs. This historical
run does not contain the unpublished fixes. The connector's commit-run wrapper
returned no runs because it filters to pull-request events; this was not treated
as evidence that CI is absent. The specific run's 17 job records were read instead.
No new hosted pass is claimed and no workflow was rerun.

## Remaining issues

Recommended execution order: **F1, F4, F5, then F2/F3**, followed by the usability
recommendations. No application fix or additional live scan was executed after
these findings; preserve this failed/partial pair when verifying the next change.

### F1. High: intermittent local interface queries stop useful scans

Both live jobs stopped with the exact `list_timeout` reason from
`app/config.py:nmap_interface_diagnostic`, which gives local `nmap --iflist` five
seconds. Light retained two completed checks; Deep's active process was cancelled.
There is no evidence here of an actual network change. Three subsequent local-only
interface queries succeeded in 1.728/1.460/1.406 seconds, showing intermittency,
not a permanently missing adapter. Concurrent regression work was running: its
contribution is possible, not established as the root cause.

`jobs/supervisor.py` creates a separate two-second monitor for each job;
`scanner/network.py` coalesces overlapping reads within one guard, not across
different guards. Each fresh snapshot also performs local interface/connection
queries. Next implementation should measure queue/start/query durations and
process counts, share only overlapping fresh reads for compatible requests, and
recheck actual scope/adapter identity before resuming. Test slow queries, five
parallel jobs, real route changes and cancellation. Never remove the safety guard,
reuse indefinitely stale network authorisation or merely hide this error.
Live successful Light/Deep completion must be repeated after the reliability fix.

### F2. Low: device card calls a safety interruption a cancellation

The failed Deep report correctly explains the timeout at the top, but its device
card says **"Device checks were cancelled."** `static/js/devices.mjs` uses only
`service_status`, ignoring `reason_code: network_interrupted`. A reader can infer
they pressed Cancel. Prefer "Stopped because the network connection could not be
verified" for this reason; keep user cancellation distinct. This is a display
issue, not lost evidence or a completed check incorrectly marked successful.

### F3. Low: partial CVE cache wording contradicts the cache policy

Code review: `static/js/cves.mjs` always says saved checks are reused for 24 hours
when a check date exists, including partial provider searches. `api/cves.py`
correctly excludes `related_search_incomplete` from that cache. Make the date
caption conditional so an incomplete search explicitly offers a new attempt.
The fresh real provider result is reported separately; this edge is identified
from the render/cache branches, not claimed as a live provider failure.

### F4. Medium: an interrupted host attempt lacks its terminal attempt record

One unfinished Light target records `attempts: 1` but has an empty
`attempt_details` list. The report retains the global `list_timeout` and the
target's `network_interrupted` reason, so the interruption is not hidden; the
per-attempt duration/exit/outcome record is missing. In `jobs/supervisor.py`, the
attempt is counted before awaiting `_run_scanner`, while its `HostAttempt` is
appended only after that await returns. Sibling-worker failure cancels unfinished
workers in `finally`; a cancelled await can bypass that append.

Finalise each genuinely started attempt on normal return, task cancellation and
guard failure. Preserve known timing/cause and explicitly unknown exit status;
do not invent a scanner return or count queued work as an executed probe. Test a
guard failure while one worker is scanning and another returns, then reopen the
saved report and check attempt-count/detail consistency. Priority after F1,
before the smaller F2/F3 display fixes.

### F5. Medium: an intermittent WebKit navigation page error remains

The complete fresh suite exited 1 at teardown of
`test_superseded_post_never_replaces_newer_scan[webkit-409]`. Its state assertions
passed, but the page-error collector recorded `/api/running-scans ... due to access
control checks` during navigation. Progress/receipt-specific cleanup and the
preceding clean WebKit suite do not prove every read/navigation timing is fixed.
No browser error was filtered and no CORS/CSRF policy was relaxed.

Separate diagnostics: the exact original case passed three repetitions, and a
held active-scans-read navigation passed (`webkit-probe-results.xml`: four cases).
Three native-transport cases, each making five Light/history transitions without
any driver request interception, also passed (`webkit-native-results.xml`). Their
synthetic scanner/provider methods forbid real use; no scan POST was submitted.
These probes did not reproduce the error and do not identify its root cause.

Capture native request abort/continuation and navigation timing under the failing
conditions before deciding whether a product or test-fixture change is appropriate.
Focused diagnostic passes do not erase this full-suite error. Priority after F1/F4;
do not mark hosted CI green on the strength of a local rerun or remove WebKit
from the matrix. The error does not justify weakening the app's origin policy.

## Recommendations from reading the reports as a novice

1. **Lead failed reports with what could not be assessed.** The failed Deep
   overview currently begins "0 devices"/"0 features that answered". The title,
   coverage and empty-findings notice correctly say incomplete, but a better lead
   is "The device check stopped before results were available. Its security has
   not been assessed." Keep factual zeros in technical details.
2. **Reduce empty-report controls.** Deep shows search, sorting, five zero-count
   priority filters, an empty detail panel and a zero-task checklist. Use one clear
   explanation and the safe retry action, with technical evidence still accessible.
   Several repeated incomplete-scan cautions can be consolidated without hiding
   incomplete coverage. This is simplification, not a new navigation redesign.
3. **Separate found addresses from checked device results.** Light says six
   matching device results and then explains that four have no usable result.
   Lead with "6 addresses found; 2 checked; 4 unfinished" in the device count.
4. **Explain naming and optional enrichment coverage.** Both completed Light
   devices had reverse-DNS timeouts; no mDNS observations were recorded and later
   name/detail enrichment was interrupted. Missing names do not show that discovery regressed
   or that an intruder exists. Distinguish not-run/interrupted/no-response for
   optional name/certificate checks and offer an explicitly bounded naming retry.
5. **Give the live helper separate flow and scan-coverage outcomes.** Its existing
   zero exit after a correct failed-report workflow is useful for UI acceptance
   but easy to misread. Emit distinct `flow_passed` and `scan_pair_completed`
   summaries and an opt-in requirement for complete scan coverage. Preserve failed
   reports for inspection rather than skipping their UI checks.
6. **Complete participant, real assistive-technology and Ubuntu lab evaluation.**
   Automated wording validation checks factual constraints, not whether a novice
   understands the actions. The actual AI chooses/validates reviewed wording;
   neither it nor these tests independently proves device safety.
7. **Group repeated interruption notes on narrow screens.** In the 390 px Light
   screenshot, the same network interruption is repeated for four addresses and
   pushes the retry action below the first screen. Show the cause once, a short
   affected-device count/list and the retry action together. Keep per-device
   attempt details expandable and preserve the incomplete-coverage headline.

## Organisation review

Application module, template and static-asset reachability checks passed. No new
orphan application file was demonstrated, so no source or historical evidence was
deleted. Existing pure CPE, validation, scan-start state and lifecycle boundaries
remain useful. A shared fresh network-observation coordinator is a focused next
change; a framework or database rewrite is not supported by these findings.

Final integrity check: all 274 frozen source/test/script/workflow/lock files stayed
unchanged, all 853 normal evidence files stayed unchanged, and whitespace checks
passed. Only documentation and ignored private diagnostic artifacts were added or
updated by this execution. No fixes, commit, push or hosted rerun were performed.
