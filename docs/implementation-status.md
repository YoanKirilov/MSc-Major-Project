# Implementation brief status

## UI/UX reliability and recovery — 14 October 2026

[Execution and verification](ui-ux-implementation-20261014.md) track the research
IDs individually. Implemented stable job controls/focus, distinct report deletion
identities, zoned dates and explicit UTC filter dates, persistent Settings feedback
and dirty/discard/leave protection, authenticated recovery browsing after reload,
recovery storage/backup coverage, wording provenance, per-tab search/page resumption,
role-aware beginner wording, forced-colour states and opt-in device theme.

Offline checks passed 658 Python/five Windows link-privilege skips, 195 JS,
Ruff/158-file formatting and twenty shipped syntax checks. Focused Chromium/Firefox
UX retests passed ten cases, and the new report disclosure/reflow cases passed two;
fifty older History cases passed in the broader run. Final package verification
passed six pages, 21 assets and synthetic report removal/recovery/restore, with
clean build/runtime dependency checks. These are scoped results, not accessibility
certification. Physical devices, actual assistive-technology speech and novice
participant comprehension remain pending. Live results are recorded separately.

## Bounded report pages and deletion - 13 October 2026

[The new execution record](report-management-20261013.md) supersedes the repeated
next-report controls and unbounded history list with at most 24 reports per numbered
page, zero initial rows/requests and one-at-a-time cached reveal. Current-page shown
selection supports confirmed individual/bulk deletion and last-batch Undo; hidden
rows and running reports are not implicitly selected. Session/CSRF, scan/notes
revisions, active AI/job admission, safe paths, bounded waits and recoverable atomic
folder moves protect the backend. Shared nicknames/settings are not erased.

Recovery files remain private and on disk (1,000 entries/2 GiB, no automatic purge);
the 13 October saved-size/export allowlists did not include `.trash` (superseded by
14 October recovery accounting/backups above). Immediate Undo can be lost on
page refresh/navigation without losing the recovery archive. Focused backend checks
passed 54 cases with five actual Windows symlink tests skipped for missing privilege;
simulated junction guards passed. The final offline gate passed 653 Python/190
JavaScript cases with five link-privilege skips and 91 deselections, Ruff/154-file
formatting and eighteen syntax checks. Installed functional checks passed six pages,
nineteen assets, synthetic report create/reopen/delete/Undo and demo reopening;
both dependency checks were clean. All 96 installed application files match source.
The final scoped Chromium/Firefox matrix passed all 50 cases with no assertion or
cleanup failures. Earlier 49 passes/one first-paint harness failure and the next
run's 50 passing bodies/two Firefox teardown errors are preserved; both harness
issues were corrected without scripted scroll/loading or exception suppression.
Three affected Firefox retests passed before the final clean matrix. Six affected
colour/settings/library/synthetic-workflow regressions passed in 97.48 seconds;
final Ruff/154-file formatting rechecks passed after fixture cleanup. WebKit remains
blocked/unverified. Allow active jobs to finish, restart the backend task and reload
the browser for the new routes/UI.
The Python-3.11-compatible junction fallback was exercised synthetically on Windows
3.14, not an actual 3.11/Ubuntu run. Prior counts below are dated evidence, not this
change's verification. No live scan or existing-report deletion ran.

## Combined usability improvements — 13 October 2026

[The execution record](design-polish-20261013.md) implements the prior remaining
running-copy/action-spacing issues and all five design priorities: global display
preference discovery, compact saved-device choices, end-of-list paging, task-progress
semantics and report action hierarchy. Related fixes improve missing-address error
focus, cancellation-error recovery, unchanged live-region messages and unreadable-row
keyboard focus. Offline checks passed 602 Python/158 JavaScript; final installed
assets match all 93 app source files. Chromium/Firefox browser evidence is recorded
there separately. WebKit is blocked before page creation by Windows App Control,
not counted as validated. Final affected Chromium/Firefox retests passed; the
initial broad failures and Windows teardown flake are preserved in the record.
The callback remains a runtime investigation, not claimed fixed by UI changes.
No live scan/provider or normal data write ran.

## Stable home progress — 13 October 2026

[The fix and design review](home-progress-position-20261013.md) removes progress-card
promotion and automatic scrolling on start/reconnect. Progress remains below setup;
the setup's top alignment stays consistent even on tall displays. Scan admission,
parallel jobs, saved data and AI/scanner contracts are unchanged. The record separates
verified evidence from proposed next design work: 602 Python/138 JavaScript and
31 selected three-engine browser cases passed, plus installed-package checks.
Visual review identified stale running/readiness copy and tightly spaced desktop
progress actions as remaining follow-ups; neither is claimed fixed by this change.

## Zero-start reports and accessibility — 13 October 2026

[The execution record](report-accessibility-20261013.md) supersedes the earlier
eight-entry history batches and justified-alignment option. Opening/searching
history starts empty; intentional scrolling reveals one report at a time, with
an explicit first-scroll keyboard control. Light/Deep title colours stay tied to
profile and reverse on hover/focus. Dark/Light, larger text and reduced movement
replace alignment; saved facts and reading filters/disclosures remain separate.
The record distinguishes focused passes, broad-run old-contract/launch failures,
their retests and final package/offline evidence. No live scan/provider ran.

## Home setup and progressive history — 12 October 2026

[The execution record](home-history-ux-20261012.md) covers a cohesive home-page scan
setup, removal of duplicate Light/Deep entry links, and eight-report batches as the
reader scrolls. Both scan modes, compatibility URLs, parallel jobs and safety checks
remain. Native Load more/retry controls preserve keyboard access and loaded results;
filters search the full library. No live scan or provider call is part of this UI
task. Finished-source verification is recorded in the linked execution record.

## Final-only wording and supporting row — 12 October 2026

[The latest execution record](report-layout-final-wording-20261012.md) covers removal
of duplicate original/previous prose from the interface (not JSON/evidence), the
responsive desktop supporting row, a shared 1360-pixel shell, shorter source labels,
polite review-count feedback and accurate empty-task messages. Focused three-engine,
offline and installed-package checks passed. New Light checked 9 of 10 discovered
devices, retaining one unreachable address after two attempts; Deep completed this
PC without scan errors. Raw/AI replay passed. Final live-report/full-gate status and
the continuing runtime/manual-evaluation limits are recorded there.

Final full gate: 732 Python/browser and 111 JavaScript passes. The actual-report
viewer passed 16 responsive combinations with zero page errors or extra scans/
edits, and evidence hashes were unchanged. Original wording is hidden only from
the interface, not deleted from saved results. Refresh a report to see the changes.

Read the newest sections first. Older dated sections preserve what was pending at
that time; they are not the current outstanding-work list.

## Same-day UI/UX repeat follow-up — 12 October 2026

[The repeat execution record](ui-ux-live-followups-20261012.md) records findings
before edits and maps them to readable technical-table controls, honest task
availability/empty-filter feedback, visible saved task status, a refresh-safe review
device filter and shared context for repeated unidentified replies. All findings
and independent actions remain available; JSON evidence and scanner rules are unchanged.
New Light and this-PC Deep checks completed without scan errors, and evidence/AI
replay plus actual-report cross-browser checks passed. Full regression status and
remaining runtime/manual-evaluation limits are tracked in that record.

A new verification-only fault was also fixed: browser fixtures now reserve a safe
high-ephemeral loopback port rather than occasionally receiving a browser-blocked
low port. This changes test setup, not the application's port or scan architecture.

The final full three-engine gate passed 726 Python/browser and 110 JavaScript tests;
offline installed-package verification passed, with all 91 packaged app files
matching source. The earlier test setup error is retained separately. The five UI
changes and test-harness fix are complete; the runtime/manual-evaluation limits
listed in the execution record are not marked resolved.

## Beginner-reading follow-up implemented — 12 October 2026

[The execution record](readability-fixes-20261012.md) maps the findings-file addendum
to implemented scan/progress read recovery, exact-address search, unknown-result
previews, grouped device evidence and the requested compact/justified novice reading.
Visible purpose explanations, identification/term help and web-page precautions keep
facts and uncertainty separate from advice. Approved Ollama wording is version 4.3.0.

The complete three-engine synthetic gate passed before two additional display-text
clarifications; the final source then passed fresh offline and saved-live-report
three-engine checks. New authorised Light and this-PC Deep scans completed without
scan errors, and evidence/AI replay passed. No original reports were rewritten.
The intermittent upstream Windows cleanup warning has been investigated but is not
marked fixed. Real-reader, physical-device, Ubuntu and actual provider evaluation
remain separate work; Pi-hole remains deferred.

## Repeat live review — 9 October 2026

[The repeat review](live-ui-repeat-20261009.md) saved new isolated Light and this-PC
Deep reports. Light retained one unreachable device after two attempts (9/10 checks
finished); Deep completed without scan errors. Evidence/AI replay, automatic report
opening, refresh, history/Run again, three-engine responsive checks and the fresh
offline gate passed. No application-code fixes, upgrades or removals were made.

Storage-read recovery and exact-IP search remain pending. The new failed-device
case also supports replacing a zero-feature preview with explicit “Not assessed”
wording. The earlier Windows close issue was not seen this time but is not marked
fixed. Contextual help, shorter mobile headings and guided novice actions/identification
remain recommendations, with real-reader/physical-device evaluation still required.
Normal reports/backend were preserved; Pi-hole and real CVE lookups remain deferred.

## Live review after UI follow-ups — 9 October 2026

The authorised Light and this-PC Deep runs completed with zero scan errors and no
unfinished device checks. Evidence replay, AI validation, refresh/history/Run again,
three-engine responsive report checks and a fresh offline gate passed. See
[the dated review](live-ui-review-20261009.md) for exact counts, isolated report locations,
intermediate harness failures and verification limits.

New pending work: helpful recovery for generic scan/progress storage-read I/O errors,
exact full-IP search/recognition, investigation of the reproduced Windows socket-close
diagnostic, and the proposed contextual-help/device-focused UI refinements. These are
not implemented by this review. Nontechnical-reader and physical-device testing remain
open; Pi-hole remains deferred and no real CVE lookup was performed.

## Eight UI/UX follow-ups implemented — 9 October 2026

The [follow-up record](ui-ux-followups-20261009.md) maps all eight changes and their
verification. Reports recover per-tab reading state, use consistent feature-specific
review titles, separate missing facts from zero observations, and keep comparisons/
announcements with their device. Concise progress status, sized section navigation,
persistent task collapse, visible practical directions and purpose-first scan choices
retain the current visual identity, JSON evidence and revision-safe notes.

Focused browser/workflow and final installed-wheel checks passed. The final complete
offline three-engine gate passed **688 Python/browser and 102 JavaScript tests**, with
lint/format and all 15 module syntax checks. Normal reports/backend and earlier unrelated
runtime/live-provider/Pi-hole limitations are unchanged. Manual phone, screen-reader,
reader-study and Ubuntu verification remain open.

## UI/UX brief implemented — 9 October 2026

The [28-item UI/UX brief](ui-ux-review-20261008.md) now has a
[finding-by-finding implementation record](ui-ux-implementation-20261009.md).
Device anatomy, mobile detail placement, search/checklist scope, shared navigation,
forms, modal editing, focus and supporting-information placement are implemented.
Separate display components and organised CSS retain revision-safe writes and
unchanged evidence. Final three-engine regression passed **664 Python/browser and
93 JavaScript tests**, lint/format and 14 module syntax checks. Fresh installed-wheel
verification and copied-report read-only audits passed. No new live scans or real
provider requests ran; normal reports and the running backend were preserved.

Physical devices, real zoom/screen-reader evaluation, Ubuntu and nontechnical-reader
measurements remain unperformed. Prepared reader tasks are in `evaluation-session.md`;
do not claim human comprehension or accessibility certification from these tests.
Earlier unrelated Windows runtime/Pi-hole/live NVD follow-ups are not marked fixed
by UI verification.

## Home reliability and date/package follow-ups — 8 October 2026

Implemented the measured Windows connection-query improvement, complete shared
UTC summary/search/device-picker policy, readable uncertain-time labels, and pinned
isolated build tools with offline-cache verification. Fixed dependency-audit includes
and added returned-coverage checks across independently validated environments.
Final offline gate passed 582 Python/74 JavaScript cases; the separate three-engine
gate passed before this tooling-only follow-up. The safety guard, saved facts,
rule severities, existing layout and JSON-only storage remain intact.

Authorised concurrent Light completed 23/24 discovered-device checks; one unreachable
device is still disclosed. This-PC Deep completed with no scan errors. Saved evidence,
all 15 Ollama records, mobile/refresh/navigation, regression, installed-package and
security checks passed. New live reports use isolated JSON; normal data was preserved.
See [the implementation and verification record](home-live-review-20261008.md).
Physical-phone/accessibility/reader/Ubuntu work and the unreproduced Windows shutdown
reset remain separate limits. Pi-hole and real NVD provider checks remain deferred.

## Offline organisation and saved-date fixes — 8 October 2026

Extracted pure CPE/fingerprint validation from NVD HTTP orchestration with compatible
old imports. Shared aware-UTC parsing corrects report-comparison ordering and prevents
bad dates from hiding usable previous observations or qualifying cross-report nickname
reuse. Added test-only live-work guards and removed two tests' hardware dependencies.
Final offline verification passed 545 Python/73 JavaScript tests, lint/format and 11
syntax checks; all source/assets remain referenced and no source file was deleted.

No live scan/discovery or real model generation ran; normal storage/backend and UI
layout were left alone. New installed-wheel verification was not completed because
offline build tools were absent. Summary/search date consistency and build reproducibility
are follow-ups, alongside the prior adapter timeout and real-user/device evaluation.
See [the execution record and recommendations](offline-code-review-20261008.md).

## Nickname and plain-language follow-ups implemented — 7 October 2026

The two confirmed frontend follow-ups from the earlier review are fixed: delayed
nickname snapshots cannot regress the displayed version, and naming help uses the
actual button label. Added reviewed Windows/VMware feature help, factual Light
scan-computer coverage and expandable duplicate mobile checklists. Nickname adoption
is a separate tested module. Final regression passed 518 Python/73 JavaScript tests,
three browsers, installed-package and security gates.

New live Light/Windows-PC Deep saved replayable evidence and validated wording;
Light had one unreachable host and Deep hit a Windows connection-query timeout
before optional enrichment. These limitations are preserved, not concealed. All
13 accepted AI records, four live widths, navigation/refresh and data integrity
passed; one Light item kept reviewed wording instead of a non-simpler rewrite.
See [the implemented plan](nickname-guidance-plan-20261007.md) and
[results, reliability follow-up and evaluation limits](followup-live-20261007.md).
The normal backend was not stopped and normal reports were not changed. No claim
of completed participant/physical-phone/Ubuntu evaluation or repaired Windows reset
is made. Earlier dated sections below describe their previous version.

## Post-restart verification — 7 October 2026

The new home Light/Windows-PC Deep verification passed scanning, evidence/AI replay,
refresh/history/navigation and responsive checks. Fresh regression passed 515 Python
and 65 JavaScript tests with three browser engines. Prior reports and the normal app
were preserved; new live reports are in isolated test storage, not normal history.
Two follow-ups remain: delayed nickname replies can regress the frontend snapshot,
and naming guidance refers to a differently labelled lookup button. No new source
fix was made in this review. See [the review and recommended next steps](postfix-live-review-20261007.md).

## Review fixes implemented — 7 October 2026

Implemented the nickname storage error boundary and locked backup recovery, Deep
refresh/active-progress fixes, explicit request bounds and clearer feature/name/action
wording. Recent compatible Light network scans can now retain a separate bounded
earlier-observation view. Original evidence, finding severity, model input privacy and
JSON storage are preserved. Added fault/concurrency, comparison and responsive tests.
See [the executable plan and verification record](development-plan-20261007.md).
Final verification passed 515 Python/65 JavaScript tests, three browser engines,
installed-wheel/security gates and real local Ollama on synthetic facts. No new
Nmap scan ran in this implementation turn; post-restart live verification is next.
The Windows reset still needs a reproduction; participant/physical-phone/Ubuntu
evaluation remains pending. Earlier dated sections below are historical evidence.

## Review fixes implemented — 6 October 2026

Implemented the four confirmed application gaps from the latest review, followed by
clearer service/role/comparison wording and user-owned checklist progress/filtering.
Annotation projection is extracted into a tested module; factual evidence, original
guidance and severity are unchanged. JSON remains the persistence system.
See [the execution and verification record](fixes-and-improvements-20261006.md).
Older sections below preserve the pre-fix review and earlier runs. The Windows
runtime reset and actual reader/phone/Ubuntu evaluations remain pending.

Verification complete: 459 Python/61 JavaScript, three browsers, installed package
and security gates passed. New Light (12 devices) and PC Deep (14 open services)
finished without scan errors; source-evidence replay and all 15 AI records passed.
Refresh, history, Run again, responsive views and live checklist persistence passed.
Generated build/cache folders were archived and removed; no source file was deleted.
Normal reports/backend were preserved. Restart the normal backend when idle.

## Live architecture review — 6 October 2026

New Light and PC Deep completed without scan errors; all 14 AI records and saved
evidence replays passed. Refresh/history, Run again and four responsive widths
passed, as did a fresh 448 Python/57 JavaScript regression with three browsers.
Additional review reproduced checklist snapshot drift, ambiguous unnamed-device
controls, inconsistent annotation/title storage error responses and an unbounded
saved-report AI retry backlog. Fixes/removals are deliberately deferred at the
user's request. No unused application file was found. See
[the review, cleanup candidates and recommended order](architecture-live-review-20261006.md).
Normal source/data/backend were preserved; the Windows reset remains open.

## Report experience recommendations executed — 6 October 2026

Implemented all four repeat-live recommendations: reported-stage Deep activity,
overview-to-device identification and visible naming controls, saved per-action
checklists, and a promoted conservative comparison section. Checklist edits use
locked, revision-protected annotations and never change scan evidence or severity.
Paired controls synchronise, stale tab edits reload saved notes, and keyboard/mobile
access is retained. Final regression passed 448 Python/57 JavaScript tests, three
browser engines, lint/format and syntax checks. No new live scan was run; normal
reports/backend were preserved. Restart the normal backend when idle to load this
implementation. See [the execution plan](experience-plan-20261006.md).
The intermittent Windows socket-reset runtime issue remains unresolved.

## Second live verification — 6 October 2026

Both profiles completed successfully again. Light checked six devices, while PC
Deep returned 15 open services; neither had scan errors. All 13 AI records, saved
evidence, refresh/history, responsive layouts and Run again passed. No new bug was
observed. Suggested next improvements: step-based Deep progress, clearer device
identification, user action checklists and more visible comparison information.
See [the repeat evidence](live-repeat-20261006.md). Recommendations were not yet
implemented during that live run; the subsequent implementation is recorded above.
The intermittent Windows reset remains unresolved.

## Post-restart live verification — 6 October 2026

Current source completed authorised Light and PC Deep scans with no scan errors.
Eight Light devices and the Deep host finished checking; all 13 AI records and both
evidence replays passed. Refresh, history, responsive layouts, Run again and the
mobile progress fixes passed. No new application failures or backend tracebacks
were observed. This used a separate test instance; it does not certify the running
normal app instance or add reports to its history. The intermittent Windows reset
remains open. See [the evidence and recommendations](live-check-20261006.md).

## Follow-up plan executed — 5 October 2026

Mobile percentage wrapping, simpler waiting messages and device-role context in
suggested actions are implemented and verified: 442 Python/56 JavaScript tests and
three browser engines passed. The Windows socket-reset path was checked against
installed Python 3.14.2 and upstream 3.14; no verified supported fix was identified.
Diagnostics remain enabled; this dependency issue is explicitly not marked fixed.
See [the execution plan](follow-up-plan-20261005.md). No network rescans or changes
to normal report storage were made.

## Reliability and usability improvements — 5 October 2026

Implemented bounded subprocess pipe cleanup, validated annotations-backup recovery
with corruption quarantine and revision safety, live scanner activity, compact
mobile device cards, report navigation and recorded gateway/scan-computer roles.
Added scoped Windows runtime diagnostics without suppressing exceptions; the
underlying shutdown-reset issue is diagnosed, not claimed fixed. Verification:
442 Python/53 JavaScript tests and three browser engines passed. Fresh Light saved
9 checked devices plus one unreachable target; Deep completed with 15 open services
and no scan errors. All 14 AI records and both evidence replays passed. One minor
mobile percentage-wrapping issue and simpler progress wording remain follow-ups.
See [the implementation and live report](improvements-20261005.md). Normal data and
backend were preserved; restart the normal task when idle to load the changes.

## Live verification and focused cleanup — 5 October 2026

The updated network guard completed both authorised live profiles without the
previous interruption. Light: seven devices/ten open services/seven review items;
PC Deep: one device/14 open services/four informational review items. All 13 AI
records and XML replay passed. Removed the redundant private adapter-query fallback
branch and consolidated imports; no source files were deleted. Final checks:
433 Python/51 JavaScript tests and three browsers passed. A Windows connection-reset
callback traceback is a remaining diagnostic follow-up, not a scan failure. See
[the live report and improvements](live-check-20261005.md).


## Network diagnostics and unfinished report counts — 4 October 2026

Overlapping Windows network queries are shared without a stale cache; guards still
stop on unavailable or changed context and now preserve diagnostic reasons.
Safety cancellation retains its origin at host/attempt level. Headlines and AI
wording include cancelled/unstarted checks in unfinished counts. Prompt 4.2.2 and
updated asset versions avoid presenting older wording as current. Verification:
427 Python and 51 JavaScript tests plus three browsers passed; real concurrent
adapter-query check passed. A new full live scan is not claimed. See
[the fix report](live-recheck-fixes-20261004.md). Restart the backend when idle.


## Self-scan and cancellation remediation — 4 October 2026

Windows exact self-targets now use automatic local Nmap routing while remote
targets and the network guard keep their original interface binding. Self-scan
reports disclose the local-observation limitation. Pre-cancelled process work no
longer spawns, and cancellation-watcher cleanup is awaited. Final verification:
409 Python/50 JavaScript tests, three browser engines and installed package passed.
The live PC Deep scan completed with 14 open services, five review items and six
validated AI records. See [the evidence](scanner-fixes-20261004.md). Normal data and
backend were untouched; restart the normal task when idle to load the code.

## Architecture organisation — 4 October 2026

Extracted report-state transformations into `jobs/transitions.py` and protected
admission from duplicate active IDs. No source files were deleted. 396 Python and
50 JavaScript tests, three browser engines and installed-package checks passed.
Live Light completed; the standby/off Sony Deep run was cancelled and saved honestly.
An awake-TV Deep run remains pending. See [the review](architecture-review-20261004.md)
for scope, exact evidence and test-data isolation. Restart the normal backend task
when idle to load the code changes; it was intentionally left undisturbed.

## Remediation and live verification — 3 October 2026

Implemented the [review plan](development-plan-20261003.md): bounded queue versus
execution budgets, shared discovery/host capacity, network-change interruption,
structured Windows scope detection, conservative CVE dictionary resolution,
validated AI wording precedence, service-level CVE controls, annotation snapshots,
per-attempt diagnostics, fairer bounded mDNS naming and offline backup/restore.
Current structure is documented in [architecture-current.md](architecture-current.md).

Final regression passed 394 Python and 50 JavaScript tests, three browser engines,
lint/format and installed-package verification. Live Light checked 11 of 13 devices;
two remained unreachable after bounded retries. Evidence replay and mobile checks
passed. Sony Deep completed on its first attempt: 15 open services, nine review
items and all ten AI records accepted. Both evidence replays, refresh/history and
Run again navigation passed; 147 prior scan JSON files remained unchanged. See the
[current live record](live-check-20261003.md) for honest coverage, the raw-evidence
filename defect found and fixed during testing, and outstanding evaluation gates.
The previous dated sections below are retained as historical evidence.

## Latest home verification — 2 October 2026

Completed the requested normal-app Light scan and a successful Sony Deep scan;
preserved a separate sleep-interrupted Deep attempt. Light checked 12 of 13 discovered
devices; one remained unreachable. Fresh Deep checked the Sony on its first attempt,
with 15 open services, nine review items and all ten AI records ready. Saved evidence
replay, history, refresh, mobile widths and Run again checks passed. All 42 previous
reports remained unchanged. See [the detailed live check](live-check-20261002.md).

Fixed CVE-button eligibility, added page/asset reachability regression, and archived
only generated build/cache folders. Final verification: 377 Python and 50 JavaScript
tests, three browser engines and installed-wheel checks passed. The app retains local
JSON storage; no SQLite or Pi-hole deployment was introduced.

Remaining priorities found live: resolve outdated CVE product identifiers using
authoritative dictionary mappings, and explain laptop-sleep interruptions explicitly.
Empty exact-CPE searches can currently miss references after product naming changes;
this is not a clean-bill-of-health result. The prepared report remains accessible
when a scan cannot finish.

## CVE references — 2 October 2026

Implemented and activated the [CVE reference feature](cve-references.md). Findings
offer NVD source links and an explicit software/version lookup when saved Nmap CPE
evidence is sufficient. Local Ollama selects reviewed match-context explanations;
it cannot create IDs, links or vulnerability findings. References persist separately
in report annotations, with caching, timeouts, retry and clear unavailable/no-match
states. Light and Deep both preserve CPE evidence on new scans. Old reports remain
readable without that field. Regression, browser, installed-package and real public
NVD/local Ollama checks passed; the normal backend was restarted and its saved-report
UI verified. All 42 prior report hashes were unchanged. See [testing](testing.md).

## Running app and network recheck — 2 October 2026

Restarted the verified idle old backend and confirmed the current API is running;
41 previous reports were preserved. The later normal home Light run completed
analysis, with one unreachable device retained as incomplete coverage. A subsequent
connection change to the previously unauthorised network is now shown clearly:
Check network again refreshes status without submitting a scan. All 27 dashboard
tests and actual authenticated Chromium checks passed. See [testing](testing.md).
The prior backend-restart handover below is superseded; reload for the final UI change.

## Network recovery — 1 October 2026

All eight steps in the [network recovery plan](network-recovery-plan-20261001.md) are
implemented: Windows gateway parsing, normal saved-scope correction with backup,
Automatic/Manual controls, confirmed-scope admission, actionable mDNS diagnostics,
bounded honest AI readiness checks, Light timing guidance and clearer service labels.
The normal app now uses the authorised `192.168.1.0/24`; saved scan evidence is unchanged.
353 Python and 48 JavaScript tests, three-engine browser checks and fresh packaged
installation passed. Restart the backend after active jobs finish and hard-refresh
for new routes/assets. No new live scan was run during this implementation.

## Library reliability — 1 October 2026

Implemented target-preserving Deep picker refresh, last-check context, separate
unreadable-report warnings, accurate no-match wording and a bounded per-instance
compact search cache. The [execution plan](library-improvements-plan-20261001.md)
records verification and the live-test gate. Reader/physical-device protocols were
extended, not presented as completed evaluations. No new live Light or Sony Deep run
is authorised on the currently connected ANGLIA.LOCAL network.

This is the handover for the eleven agreed items. Verification details are in
`testing.md`; external evaluation steps are in `evaluation.md`.

## Report fixes and Pi-hole scope - 30 September 2026

Implemented stacked unfinished-check notes (including narrow screens), explicit device
addresses on comparison cards, visible name-lookup outcomes and local failure feedback,
and the search label "Search devices and results". A version mismatch now explains how
to restart the backend before starting a new scan; existing-job recovery remains available.
Pi-hole deployment/evaluation is deferred to [future improvements](evaluation.md), not
an outstanding requirement for the current assessment. The inactive connector is retained.
Verification and the requested single-Sony Deep scan are recorded in `testing.md`.
The [Deep run](deep-sony-20260930.md) completed with fresh mDNS naming, 15 open services
and nine review items; original normal reports were preserved in the isolated workflow.

## Experience and discovery improvements - 30 September 2026

All seven steps in [the implementation plan](experience-improvements-plan.md) are implemented:

1. Multiword search across findings and devices, including devices without findings,
   with visible counts and Clear search.
2. Recent saved Light-device choices in Deep setup, with dates, uncertainty and manual entry.
3. Per-job running overview, progress/report links and explicit cancellation.
4. Server-filtered history and optional report titles stored separately from scan evidence.
5. Revision-based nickname updates in already-open, visible finished reports.
6. Explicit, authorised and bounded reverse-DNS/optional-mDNS name refresh with provenance.
7. A visible panel for existing cautious historical comparisons.

Original scan evidence remains unchanged by titles/name refreshes. Optional annotation
failure leaves factual results visible with an explanatory notice. Synthetic regression,
responsive and packaging evidence is recorded in [testing](testing.md). No live scan,
real DNS/mDNS verification, model call, Pi-hole deployment or normal report migration
was performed. Reader evaluation, physical-device checks and large-archive performance
remain external follow-up work. Restart the backend after active jobs finish and reload
the browser to use the new routes/assets.

## Five active jobs with quiet capacity handling - 29 September 2026

Raised the default job limit from two to five. Retained two Nmap process slots and serial
Ollama preparation; more active jobs do not imply five simultaneous scanner processes.
Full pages show a neutral inline waiting status, not a capacity error alert, and poll for
availability before re-enabling Scan. Nothing is submitted automatically. The API still
enforces atomic admission and returns HTTP 429 for races; the dashboard handles it quietly.
Existing explicit APP_MAX_CONCURRENT_SCANS overrides still take precedence over defaults.

## Independent Light and Deep pages - 29 September 2026

Added `/light` and `/deep`, backed by the same template, API and JSON storage. Each page
fixes its profile, has its own pending-job key, and retains its route on refresh. Merely
opening a page does not start a scan or attach to the other profile's job. Pasted links
to a mismatched profile are redirected to the general progress page. Existing root setup
and Run again navigation remain compatible. No second process, SQLite migration or
nickname merger is introduced; existing nickname identity matching/locking remain intact.
Restart an older running backend to register the routes; no running instance was stopped
as part of implementation. See `testing.md` for final verification results.

## Report layout restored; parallel scan tabs - 29 September 2026

At the user's request, first-action guidance is back in the original Understanding your
results card rather than a new panel above statistics. Responsive fixes and factual labels
remain. The dashboard offers a new-tab setup while a job runs; each started tab is pinned
to its own scan ID for refresh/progress/cancel. Light and Deep use the existing shared API,
two-job default admission and bounded scanner resources. No extra backend instance or
database is needed. Ollama preparation remains queued rather than running models in parallel.
See the latest `testing.md` entry for synthetic concurrency/browser verification.

## Usability and release-check improvements - 29 September 2026

Implemented first-action placement, checked/discovered counts, precise completion wording,
stable finding ordering and simpler labels. Original evidence and AI provenance remain
available. Responsive coverage now includes phone/tablet/desktop sizes in Chromium,
Firefox and WebKit, with keyboard, text-size and selected touch-emulation checks.
Added pinned local security gates and a copied-backup recovery drill; updated vulnerable
development test dependencies without changing runtime pins. See the dated results in
[testing](testing.md) and [repeatable release checks](release-checks.md).
No new network scan or change to normal saved reports was required. Physical devices,
real reader-study results, remote Ubuntu CI and actual Pi-hole evaluation remain pending.

## Quality management baseline established - 28 September 2026, evening

The [quality plan](quality-plan.md) now defines project-specific standards-informed
criteria, owners, risk/release controls and executable verification steps; the
[matrix](quality-traceability.md) links requirements to code/tests. The
[new execution record](quality-evidence-20260928.md) contains the subsequent real Light
scan, local Ollama, browser, evidence replay, regression, package and data-preservation
results. It explicitly does not claim ISO certification or completed user evaluation.
No source refactor was needed for this baseline; focused count/mobile and maintainability
improvements are recorded for the next change, separately from pending external checks.

## Dashboard startup recovery completed - 28 September 2026

Reproduced a permanently disabled Checking scanner button when a cached pre-change
module lacks the new setup export. Page scripts and dependencies now use a coordinated
cache-busting version, local responses disable caching, and an independent startup
guard offers Reload page on module failure. API/session requests have a bounded wait
without automatic write retries. Full browser/offline checks passed (306 Python,
31 JavaScript). No scan or backend restart was performed. Hard-refresh the browser;
restart the backend once to enable the new cache headers. See `testing.md`.

## Run again navigation completed; Pi-hole host choice pending - 28 September 2026

Run again now returns Light scans to the starting page. Deep scans first ask whether
to reuse the previous device address or choose another, with Cancel/Escape available.
No scan starts on navigation; users confirm the setup and press Scan. Current scope is
still validated by the backend. Light known-host lists remain visible and reusable.
An active backend scan is resumed rather than duplicated; stale completed-tab storage
does not bounce setup back to the old report.

Verified with 305 Python tests (including synthetic browser workflow), 29 JavaScript
tests and a final mobile-dialog browser rerun. Existing reports are not modified.

Pi-hole app integration is present, but there is no configured service. This Windows
machine lacks Docker/WSL. Await the user's choice of an authorised Linux VM/Raspberry
Pi or Windows container setup before installing system components or creating secrets.
No router DNS/DHCP changes are authorised by this handover. See `pihole-setup.md`.

## Latest fixes and improvements completed - 27 September 2026

1. Browser validation errors show readable field messages, not object strings.
2. Blocked session storage no longer stops startup: an in-memory token and visible
   notice preserve the authenticated request flow. Session expiry remains explicit.
3. Old AI records cannot claim current successful review while their wording is hidden;
   a ready summary requires matching current overview and finding records.
4. Successful Nmap output explicitly recording one unreachable target is distinguished
   from malformed output. Both profiles retain bounded retries and missing coverage.
   No historical result was silently reclassified.
5. Read-only report presentation consistently prefers reviewed plain-language choices,
   including zero-finding reports, while preserving original guidance and AI audit.
   Device cards list observed features. Confirmed web services get address-bar help
   and warnings against credentials over HTTP or bypassing certificate warnings.
6. Saved AI progress records waiting/preparing/finished, total/completed/active counts
   and batch attempt. Refresh restores the counts; fallback records are not counted as
   successfully prepared. Existing reports without this optional field remain readable.
7. Settings/report locks have a five-second acquisition limit. API contention returns
   a readable 503 with `Retry-After`; it does not bypass locks or replace prior evidence.
   Transient background storage contention is not misreported as a scan time limit.

Verified: **306 Python tests, 24 JavaScript tests**, browser workflow, real local Ollama
on synthetic facts, installed wheel, and desktop/mobile review of a prior home report.
All 30 production reports were validated read-only. No new network scan was run.
See `testing.md` for artifacts and outstanding external evaluation.

Restart **NetGuard: Start backend** once to load the backend changes. New host checks
and AI preparation save the new diagnostic/progress fields; reopening saved reports
uses the clearer display without modifying their observations or historical errors.

## Beginner-report implementation brief completed — 26 September 2026

1. Partial AI records remain retryable. Accepted fields/list entries are frozen on
   retry; failures retain original guidance and a visible retry action. A stricter
   reviewed-choice output schema preserves list order and lengths. The existing
   two-attempt batch and overall analysis time limits remain in force.
2. Replaced the count-based red ring with neutral counts and a priority breakdown.
3. Replaced normal-view field paths with ordinary labels. Validation codes are in
   expandable technical details; completed preparation no longer shows a redundant button.
4. Grouped repeated next steps by rule/action and affected devices, made identification
   the first step, reduced repeated card text and duplicate coverage statements.
5. Relevant saved web-upgrade checks appear beside finding explanations for either
   profile, with starting-page/time limitations. They are explicitly saved checks,
   not new AI conclusions; raw metadata and identifiers remain outside model input.
6. Added editable/removable, explicitly user-assigned nicknames in separate local JSON.
   Same-report assignments work without a MAC. Reuse requires a matching network scope,
   a unique matching MAC in both reports, a finished earlier source within seven days,
   and one unambiguous nickname anchor. Editing does not extend the source age.

Verified: **288 Python tests, 18 JavaScript tests**, browser workflow, synthetic local
Ollama, fresh installed wheel, and a disposable copy of the real report. In the latter,
all **16 rejected fields resolved in two requests**, with accepted wording, facts and
the original report unchanged. See `testing.md` for artifacts and limitations.

Restart **NetGuard: Start backend** once to load the changes. Older partly simplified
reports offer **Retry remaining wording** without rescanning. Nicknames are entered via
**Add your own nickname** on device cards; clear the text to remove an assignment.
Nickname changes affect annotations only, never scan evidence or AI input.

No new network scan, Pi-hole installation, SQLite migration, commit or push was done.
Ubuntu/remote CI, live Deep/Pi-hole and participant comprehension remain unverified.
Next checkpoint: review the revised page with nontechnical readers, then confirm the
current authorised home network before any further live collection.

## Remaining implementation follow-through - 26 September 2026

- Added persisted `enrichment` progress before name/detail collectors; dashboard refresh
  resumes this stage without launching another scan. Both scan profiles share it.
- Added clearly rule-based device cards, including unfinished targets with no parsed
  device result. Historical names, conflicting names and coverage limits remain explicit.
- Ollama retries only rejected items, preserving accepted text. An invalid batch does
  not suppress attempts for later findings; outages and overall deadlines remain bounded.
- Nmap validation failures now include reviewed diagnostic text. The previous live host
  failure cannot be reconstructed without its missing raw output; no cause is invented.
- Added pinned-action Windows/Ubuntu CI and a fresh installed-wheel verifier. No commit,
  push or remote CI run was performed; Ubuntu validation remains pending.
- Added a participant-session guide and empty results template. No participant study
  has been conducted. Pi-hole still requires an actual installation for live validation.

Restart the backend once to load the changes. No running user app was restarted and no
saved user reports were modified. This work used synthetic scans and local Ollama, not
a new home-network scan. See the newest testing entry for exact verification results.

## Naming reliability follow-up - 25 September 2026

Compared the two latest user reports: both had 11 devices, but names fell from three
to two because the TV's mDNS advertisements were absent in the newer report, despite
the same recorded MAC. No collected advertisement was dropped at name assignment and
the eight-host cap was not reached; timing is a plausible contributor, not a proven
sole cause. mDNS collection now uses nonblocking concurrent lookups, a four-second
window and a bounded retry. Friendly-name TXT data and advertised hostnames supplement
instance labels. Recent direct names can be reused only as visibly historical labels
under same-scope/MAC, age and ambiguity guards. See the latest testing entry for results.

## Follow-up review and organisation - 25 September 2026

Fixed four confirmed edge cases: empty UPnP metadata, history comparisons with missing
port selections, optional failures mislabelled as timeouts (and blocking another lookup),
and guessed service identities increasing device-type confidence. Each had a failing
regression test before its fix. Enrichment coordination now lives in `jobs/enrichment.py`;
pure fact formatting lives in `scanner/observations.py`, separate from network requests.
All application modules remain referenced; no source files or saved reports were deleted.
See the newest `testing.md` entry for the final rerun and remaining external validation.

## Richer Light and Deep device information - 25 September 2026

Implemented the six agreed additions in the shared pipeline: richer optional mDNS,
conservative evidence-based device types, bounded UPnP descriptions, HTTP-to-HTTPS
checks and certificate dates, selective NetBIOS names, and recent-report comparisons.
Both profiles collect and display these under **More about this device**. Deep remains
single-host; advertised services never become confirmed open ports merely from an
announcement. Limits and failed optional checks are explicit. Local JSON and existing
reports are preserved; no Pi-hole service was installed or configured.

See the current verification entry in `testing.md`. Earlier live results below predate
these richer collectors and must not be treated as their live-network validation.

## Latest live check — 25 September 2026

Home Light scan and Ollama processing now verified: all 12 discovered device checks
completed, with 13 open services and 8 review items. See [results and follow-ups](live-check-20260925.md).
Pi-hole is still not installed/configured here; no live name extraction is claimed.
The check found a timing-sensitive test and user-facing AI fallback wording to improve.
This was a verification pass, not another application-code change.

## Pi-hole setup implementation — verification deferred (25 September 2026)

Prepared `deployment/pihole/compose.yaml` and its opt-in home DNS profile. The base
deployment is loopback-only, requires a private administrator-secret file, disables
DHCP/NTP serving and does not restart automatically. No container/runtime was installed
or started. NetGuard now supports `APP_PIHOLE_PASSWORD_FILE`, sanitised setup errors,
clearer unverified-connection wording, and a manual VS Code Pi-hole launch task.
See [setup and rollback](pihole-setup.md).

New regression tests cover password files and configuration-only status/settings;
test fixtures no longer inherit real Pi-hole credentials. **No tests, scans, app starts
or Pi-hole requests were run for these changes**, at the user's request. The earlier
passing results below predate this implementation.

Prepared lockfile updates: platformdirs 4.11.13, Uvicorn 0.54.0, Ruff 0.16.9. They have
not been installed or validated in the virtual environments. Existing constraints allow
them. Major dependency/test-client migrations and CI automation remain follow-up work,
not silently included in an untested runtime upgrade. Saved-report AI preparation,
real Pi-hole name extraction, home scans, Ubuntu and reader evaluation are deferred.

## Latest code organisation/recheck

The subsequent full review is in `architecture.md`; cleanup and repeatable commands are
in `workspace.md`. Added strict cache projections with fallback to saved evidence, fixed
device ownership on report recovery, and removed duplicate/blocking scope detection.
Shared status definitions were consolidated without rewriting the overall architecture.
Latest checks: **187 Python tests, 16 JavaScript tests, browser/local Ollama, lint,
formatting and installed-package verification passed**. Saved data and Git work were
preserved. Fifty old generated folders were archived and removed; the empty `front end`
folder is locked by another process and remains. Historical notes/screenshot are organised
under `docs/archive/` and `docs/reference/`. Live network testing is still deferred.

## Architecture audit fixes (25 September 2026)

Completed in dependency order, without scanning the current shared network:

1. **Network selection:** identify the real default-route network, including ranges
   larger than /24. Never silently substitute a VMware adapter. A saved/active network
   mismatch is shown and scan creation is blocked unless an explicitly selected interface
   matches the authorised scope. Invalid configured ranges produce useful errors.
2. **Storage completion:** a revision-bound `terminal.json` can persist final status when
   the primary report is full. Evidence stays unchanged, history/polling can finish, and
   subsequent writes absorb the marker. Report IDs must match their folders.
3. **Packaging:** include demo JSON in the wheel; verify demo read/create/reopen as well
   as pages/assets. Demo writes now use the atomic JSON writer. The unused empty
   `/api/demo-scans` route, debug runner entry point and orphan CSS rule were removed.
4. **Pi-hole and identity:** preserve healthy name sources when another endpoint fails;
   retain discovery MAC/name/vendor details through service checks. Sources are labelled
   accurately. Recompute conservative classification after naming, including conflicts.
5. **AI transparency:** prompt 4.2.0 records per-field validation rejection reasons and
   displays retained-original wording notices. The live synthetic test now requires a
   genuinely changed, validated meaning in both overview and finding, not just fallback.
6. **Progress and duration:** authenticated lightweight progress polling avoids repeatedly
   loading/re-evaluating full reports. Saved-report AI retries remain discoverable after
   dashboard refresh. Two host workers share a global two-process limit and a 30-minute
   host-stage budget; timeouts keep explicit incomplete coverage. AI retains its separate
   15-minute deadline including queue time.
7. **Maintenance and quality:** added offline storage audit, retention preview and explicit
   backup recovery into a new report ID. Existing files are never overwritten by recovery;
   no automatic deletion or database migration was introduced. Full configured Ruff lint
   and formatting now pass; VS Code startup tasks are no longer excluded from sharing.

Verified: **170 offline Python tests, 16 JavaScript tests, 86% Python statement coverage**,
real Edge workflow with synthetic scans, real local Ollama using synthetic facts, and a
fresh installed wheel serving four pages, seven assets and working demo endpoints.
Existing saved scans were not rewritten, deleted, or automatically sent for AI analysis.

**Next session:** at home, confirm the authorised range and one device before a live scan.
Then validate real Pi-hole name extraction with a configured instance. No live scan,
Pi-hole request, DNS lookup or packet capture was run on the unauthorised network.
Ubuntu validation and the nontechnical-reader study also remain pending. Retention is
preview-only; permanent deletion and incompatible-schema migration remain future work.

Restart the old backend using **NetGuard: Start backend** to load the fixes. For historical
reports, use **Prepare this saved report with Ollama**; another network scan is not needed.

## Follow-up reliability and readability fixes (24 September 2026)

- One OS-backed instance lock per data folder now covers startup recovery through
  shutdown. A second instance exits before it can reconcile the first one's jobs.
- JSON and raw-output writes use short, exclusively created temporary filenames.
  Backups are replaced atomically, and scan schema validation happens before writing.
  The previously failing long-path archive test now passes.
- Dashboard refresh resumes the saved scan, including AI preparation and scans that
  finished while the page was closed. Transient polling failures retain the scan ID
  and retry; a refresh never launches a new scan automatically.
- Nmap 7.991 was verified in both local Python environments. The dashboard waits for
  status and distinguishes missing Nmap, storage failure, and expired sessions.
  Session cookies/CSRF are rechecked on page load. Newly resolved scanner paths are
  passed to the supervisor before a scan starts.
- Ollama prompt 4.1.0 prefers reviewed wording for a reader without computing
  knowledge. Every catalogue sentence now has a plain-language alternative. The
  report explains services, priorities and unknowns, displays report-level next steps
  and checks, and includes a glossary. Original evidence/severity is unchanged.
- Verified: 150 offline Python tests; 16 JavaScript tests; real Edge synthetic
  workflow including refresh and expired sessions; local Ollama synthetic report.
  No live network scan was run and existing user reports were not changed.

Restart the backend once to load these changes, using the VS Code **NetGuard: Start
backend** task. Stop the old task first and use the newly printed session link.
For older reports, choose **Prepare this saved report with Ollama** to apply new
wording without another network scan. A live Pi-hole test and human-reader study
remain pending; usability improvements are not a claim of participant validation.

1. **AI in normal report flow — implemented.** Save factual JSON, prepare a report
   overview plus every finding with local Ollama, validate and checkpoint batches,
   and wait in the UI until completion. Empty and failed scans receive an overview.
   AI failures expose factual results and a retry action. Original evidence and guidance
   remain available; legacy AI-off settings no longer skip preparation.
2. **Result-size boundary — implemented.** Equal 20 MiB UTF-8 read/write limits,
   checks before replacement, and separate guidance snapshot archives. A larger primary
   result fails explicitly while preserving existing checkpoints.
3. **Failed results accessible — implemented.** Dashboard opens saved failed reports.
4. **Light known-host Run again — implemented.** Saved host lists are preserved.
5. **Technical output — implemented.** Script evidence keeps up to 1,024 characters,
   with an explicit truncation flag.
6. **mDNS wording — implemented.** Advertisements, discovery responses and service
   responses have distinct labels. Name sources and conflicts remain visible.
7. **Installation and evaluation — partially complete.** Dependency pins reconciled,
   package assets declared, saved-report history implemented, browser automation added,
   storage lifecycle and reader-study protocols written. Actual Ubuntu lab testing and
   the participant study require their environment and participants; neither is claimed
   as complete. See the current verification record for wheel-install results.
8. **Incomplete checks — implemented; live validation pending.** Up to two attempts,
   specific reasons and attempt counts, accurate unfinished counts, and a retry action
   creating a new scan of only eligible unfinished hosts. A live target must be confirmed
   because the saved and detected scopes differed during this session.
9. **Network message — implemented.** Dashboard uses the agreed generic readiness
   message; Settings loads actual configuration/detection and has no static example value.
10. **Device names — implemented for available sources.** Combine Nmap, reverse DNS,
    optional mDNS and Pi-hole labels with provenance, conservative confidence and conflicts.
    A generic router import remains dependent on a vendor API or sample client-list export;
    the evaluation notes explain the required investigation input.
11. **Optional Pi-hole integration — implemented; real instance validation pending.**
    Backend API authentication, scoped DHCP/network names, expiry and MAC matching,
    bounded requests, logout, graceful failure and tests using simulated responses.
    Set `APP_PIHOLE_URL` and `APP_PIHOLE_PASSWORD` before enabling it in Settings.

The existing saved scans were preserved. No SQLite migration, router reconfiguration,
packet capture or background network-wide scan was performed.
