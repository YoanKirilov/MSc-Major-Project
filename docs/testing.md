# Testing status

## Self-scan routing and pre-cancellation fixes — 4 October 2026

Both findings from the scanning-tools review are fixed; see
[scanner-fixes-20261004.md](scanner-fixes-20261004.md). Final verification passed
**409 Python tests**, one real-provider test deselected, **no warnings**, **50
JavaScript tests**, three browser engines and installed-package checks. A live
Deep scan of this PC completed on its first attempt with 14 open services/five
review items; all six AI records and retained XML replay passed. Refresh, history,
responsive widths and Deep Run again passed. Verification used isolated data and
its backend was stopped; the normal task needs an idle restart to load the fixes.

## Scanning-tools and self-scan check — 4 October 2026

The [latest tool check](scanning-tools-check-20261004.md) passed 397 Python and
50 JavaScript tests with no warnings and verified all 11 required Nmap scripts.
A user-authorised Deep scan of this Windows PC exposed a forced-adapter self-scan
failure; a two-port comparison reached the PC only with automatic Nmap interface
selection. A mocked diagnostic also confirmed pre-cancelled runner work still
attempts process creation. These two follow-ups remain open; the green regression
suite does not cover them yet. Failed-report persistence, AI, refresh/history and
mobile navigation passed. No unnecessary source restructuring was performed.

## Test-client warning remediation — 4 October 2026

Starlette's supported test client is now installed through the development-only
`requirements-testclient.lock` (httpx2/httpcore2 2.13.1, truststore 0.10.4), shared
by the development lock and installed-wheel verifier. Application HTTP clients
continue using the existing runtime httpx pin. Pytest treats the legacy-client
warning as an error rather than suppressing it; a dedicated test checks the client
type and a real in-process request. The dependency validator now follows included
lockfiles and rejects conflicting or non-exact pins.

The VS Code `.venv` also had Starlette 1.6.0 despite the existing 1.7.0 lock pin.
It was aligned to 1.7.0. Its test client now imports with all warnings treated as
errors, and both project environments pass `pip check`. A running backend must be
restarted when idle to load changed installed dependencies; no restart or live scan
was performed for this fix.

Installed-wheel verification passed without the warning, including six pages,
ten assets and demo read/create/reopen: `.test-artifacts/package-faf9a0cda3/`.
Full suite passed: **397 Python tests**, one real-provider test deselected, **no
warnings**, and **50 JavaScript tests**, with Chromium/Firefox/WebKit, lint/format
and module syntax checks: `.test-artifacts/checks-2dd463f127/`.
Earlier dated warning records below describe earlier runs, not current failures.

## Architecture refactor — 4 October 2026

See [the architecture review](architecture-review-20261004.md). Report transitions
were extracted and duplicate job admission was guarded. 396 Python/50 JavaScript
tests passed with three browser engines and installed-package verification.
Isolated live Light checked all ten discovered devices, with ten open services and
seven review items; evidence and AI replay passed. Sony Deep was cancelled after
the user confirmed standby/off; cancellation, saved-report navigation and responsive
checks passed, but a complete awake-TV Deep run remains pending. No normal-backend
restart or report migration was performed. These test reports use a separate folder.

## Repeat verification and task handoff — reviewed 4 October 2026

The [repeat live record](live-repeat-20261003.md) confirms Light checked ten of 11
devices (one unreachable), Sony Deep completed with 15 open services/ten review
items, AI/evidence replay passed, and all 155 pre-existing scan JSON files were
unchanged. Refresh, history, Run again and mobile widths passed. The repeated
offline suite passed 394 Python/50 JavaScript tests across three browser engines
in `.test-artifacts/checks-046c935987/`. The agent-owned idle test backend was stopped
afterwards so it would not block the VS Code Start backend task again.

## Remediation verification — 3 October 2026

Latest details: [live-check-20261003.md](live-check-20261003.md). Final full regression
passed in `.test-artifacts/checks-243fbcc4e8/`; the final installed wheel passed
in `.test-artifacts/package-5ce852931f/`. Light evidence replay and mobile checks
passed with two unreachable devices honestly recorded. Sony Deep completed with
15 open services, nine review items and ten accepted AI records; evidence replay,
refresh/history, responsive widths and Run again navigation passed. The final
Run again loading-race fix is included in the full regression and installed wheel.

See [the execution plan](development-plan-20261003.md) for the implementation scope
and pending external evaluation. Full regression after the main changes passed
**394 Python tests**, **50 JavaScript tests**, Chromium/Firefox/WebKit, lint/format
for 118 Python files and nine module syntax checks. One real-provider test was
deselected and the existing Starlette/httpx deprecation warning remains.
Artifacts: `.test-artifacts/checks-243fbcc4e8/`.

Fresh installed wheel passed six pages, ten static assets, demo read/create/reopen
and dependency consistency: `.test-artifacts/package-5ce852931f/`.
The public nginx identifier regression returned 15 candidate NVD records in 27.09s,
with original/resolved identifiers and dictionary provenance preserved. This was
reference research, not proof of a vulnerability on a home device.

Initial live Light `31f203bb-646b-4467-a3c0-309ba59e1715` exposed a raw-evidence filename
integration defect and saved an honest failed report. The storage whitelist now
accepts bounded attempt-1/attempt-2 names; 45 focused supervisor/storage tests passed
with raw retention enabled. The fresh live run completed as described above;
the initial failed report is preserved, not overwritten or counted as a pass.

## Home live scans and final regression — 2 October 2026

See [the live-check record](live-check-20261002.md) for real Light/Deep outcomes,
laptop-sleep interruption evidence, AI/evidence replay, mobile checks and the
remaining CVE product-identifier matching gap. Live tests use normal saved history;
offline suites use isolated data.

After fixing CVE button eligibility and adding template/static reachability checks,
`.venv-quality/Scripts/python.exe scripts/check.py --browser --browser-engines chromium,firefox,webkit`
passed **377 Python tests**, with one real-provider test deselected and one existing
Starlette/httpx deprecation warning, plus **50 JavaScript tests** and nine module
syntax checks. Python lint/format passed for 110 files. Artifacts:
`.test-artifacts/checks-e2e57a6589/`.

The fresh installed-wheel test passed six pages, ten static assets, demo
read/create/reopen and `pip check`:
`.test-artifacts/package-3fdfb07a8d/`.
These synthetic/provider-stub regressions are separate from the live Ollama results.

An earlier focused layout test was prevented by Windows sandbox access to its
pytest temporary directory; the elevated isolated retry passed. The preliminary
`.venv-brief` suite passed 374 tests but used an older pytest-asyncio with additional
Python 3.14 deprecation warnings. The final lock-aligned run above supersedes it.

## CVE reference lookup — 2 October 2026

Implemented the [CVE reference flow](cve-references.md): retained service CPEs,
version-specific public NVD lookup, reviewed local Ollama context, canonical source
links, explicit uncertainty, and bounded persistent reference notes. Neither ports
alone nor generated text can establish a vulnerability. Existing report evidence
and finding severities are unchanged.

Verification:

- Focused parser/lookup/AI/storage checks: **73 passed**.
- Full regression/browser run: **373 Python passed**, one live-provider test
  deselected, one existing Starlette/httpx deprecation warning; **50 JavaScript
  passed**. Lint, formatting (110 Python files), nine JS syntax checks and the
  Chromium/Firefox/WebKit workflows passed. Artifact: `checks-2be62b0c5e/` under
  `.test-artifacts/`.
- Final cached-AI retry update: **21 focused Python/browser tests passed**, including
  the added case which retries failed AI context without requerying cached NVD data.
  Artifacts: `.test-artifacts/cve-final-20261002/`. This focused rerun verifies the
  final update after the full suite; it is not a second complete-suite run.
- Fresh installed wheel passed six pages, ten assets, demo read/create/reopen and
  dependency checks: `.test-artifacts/package-fe357ab841/`.
- Live public-reference smoke test: Apache HTTP Server 2.4.49 returned 69 NVD
  records, of which five were retained. Real Ollama produced accepted context.
  The first eight-second AI limit timed out; the final bounded 40-second limit
  passed. This used a public software example, not evidence of a home vulnerability.
- Restarted the verified idle normal backend and checked its new route plus the CVE
  section on a saved report at mobile width. No browser errors, no scan submitted,
  and all **42 saved scan JSON hashes unchanged**. Evidence:
  `.test-artifacts/cve-review-20261002/running-verification.json`.

The initial restart identity check stopped before mutation because Windows appended
a trailing space to the command. A subsequent verification was initially prevented
by an automatic-approval usage-limit error. On continuation, approval succeeded,
the command was reverified after trimming whitespace, and activation completed.
Old reports without saved CPEs show an explanation and general NVD link; a new
authorised scan may collect the missing fingerprint. No current-network scan was run.

## Source cleanup — 2 October 2026

Reviewed Python imports/callback registration, template inheritance and static module
references. Removed the unused discovery-parser wrapper, obsolete score-ring and
danger-icon styles, and a duplicate report service-label wrapper. All five templates
and eight JavaScript modules remain in use. The workspace cleanup archived 91 files
before removing `build`, `.ruff_cache` and the empty `front end` folder; recovery
details are in [workspace organisation](workspace.md).

The isolated full Python/browser run passed **353 tests**, with one live-provider
test deselected and one existing Starlette/httpx deprecation warning. Chromium,
Firefox and WebKit workflow/responsive checks passed. Lint and formatting checks
passed for 104 Python files. Artifacts: `.test-artifacts/checks-57508b17d0/`.

The first JavaScript pass exposed a test-harness import alias mismatch after removing
the wrapper. Updated the harness's injected binding; no application change was
needed. All four JavaScript suites then passed **49 tests** (6 API, 27 dashboard,
14 report, 2 Live Server bridge), and all eight module syntax checks passed.
No additional live network scan, model generation, dependency change or packaged
installation was needed for this cleanup. Saved scan data and virtual environments
were not modified; source changes remain reviewable in Git.

## Running-backend recovery and network recheck — 2 October 2026

The repeated old mDNS message came from a backend that predated the source fix:
its live OpenAPI schema lacked `confirmed_scope`. After verifying all 41 reports
were finished and no Nmap process was running, restarted that specific instance.
All 41 report hashes were unchanged; the authenticated browser page reopened.
The running API now advertises scope confirmation and the new detection logic.

A subsequent home Light scan, `21da71bf-5d8f-48a6-a98f-d1c21cdfcbbf`, was accepted
by the normal app and finished with 34 discovered devices, 33 completed device
checks, nine findings and ready AI analysis. mDNS was bound to `192.168.1.60`.
One device (`192.168.1.228`) remained unreachable after two attempts; its cause
was not established. This is retained incomplete coverage, not the startup error.
The verification script did not submit this scan.

On continuing verification, the connection had changed to `10.240.108.0/22`, a
network previously identified by the owner as unauthorised for scanning. The saved
home scope remains `192.168.1.0/24`; no scan was submitted on the new connection.
Fixed the dashboard's mismatch flow: it now offers **Check network again**, makes
only a status request and restores Scan after a matching connection returns.

All 27 dashboard tests passed, including mismatch/recovery with no scan POST.
The first test invocation hit Windows sandbox `spawn EPERM`; the approved rerun
passed. Authenticated Chromium verification against the actual running app passed
with no page errors, confirmed the recheck sends no scan request, and reported
Nmap 7.991 available, Ollama ready and storage OK. Earlier browser verification
expected an idle button while another session had started a scan; it correctly
showed Scan in progress. Verification was adjusted to use the independent Light
setup page. Evidence: `.test-artifacts/network-recovery-running-20261001/verification.json`.
That artifact directory retains its original creation-date name.

## Network recovery fixes — 1 October 2026

Implemented and verified the [network recovery plan](network-recovery-plan-20261001.md).
The normal app's saved scope is now the authorised `192.168.1.0/24`, with a settings
backup and unchanged scan JSON hashes. Windows IPv6-first gateway detection now
returns that range; local mDNS binding verification returns `192.168.1.60` / `ready`.

Final full regression: **353 Python passed, one live-provider test deselected,
48 JavaScript passed**. Lint, 104-file formatting and eight module syntax checks
passed. Chromium, Firefox and WebKit workflow/responsive checks passed, including
Automatic/Manual settings persistence. Artifacts: `.test-artifacts/checks-7bba06e662/`.
Fresh packaged installation passed six pages, nine assets, demo creation/reopening
and dependency checks (`package-17e4180ae3/`). Focused tests had 63 passes.

The first full run had 352 passes and one outdated exact-error-text assertion; updated
it to check the new recovery message and both ranges, then reran the full suite.
One existing Starlette/httpx deprecation warning remains. No additional live scan,
real Ollama generation or authenticated normal-server end-to-end test was performed.
The backend was not restarted; restart after active jobs finish and hard-refresh to
use the new routes/assets. The following live entry describes the earlier pre-fix run.

## Authorised Light run on changed LAN — 1 October 2026, evening

After explicit authorisation, the current application ran Light on 192.168.1.0/24 in
isolated storage, with an explicit verified Wi-Fi interface. Normal settings/reports
were unchanged. Result: 29 discovered, 28 checked, one unreachable after two attempts,
21 open services, nine review items and ten validated AI records. Refresh, history,
picker persistence and 320/390/768/1440 px reflow checks passed. Retained evidence replay
matched 420 service states and nine findings. No Deep request was made: its device
has not been confirmed. See [results, bugs and improvements](live-check-20261001.md).

This later run supersedes the earlier network-test deferral for Light only. The run
itself did not fix the gateway parser or saved-scope mismatch; those were corrected
subsequently in the network recovery work above. Ollama was stopped initially;
local startup eventually succeeded and real
analysis completed. The initial health warning was preserved as historical evidence.

## Library reliability — 1 October 2026

Implemented the [execution plan](library-improvements-plan-20261001.md): target-preserving
picker refresh, explicit last-check uncertainty, separate unreadable-report warnings,
correct empty-search wording and bounded per-store search projections. Added cache
invalidation/budget/concurrent-read/racing-write tests and browser cases for disappearing
choices, manual targets, history filters and warnings. Original scan evidence stays intact.

Full regression: **338 Python passed, 1 live-provider test deselected, 45 JavaScript passed**,
104 Python files formatted, lint and eight module syntax checks passed. Three-engine
responsive/browser coverage passed. Artifacts: `.test-artifacts/checks-9a3285c344/`.
The final focused library browser rerun also passed, including populated device choices
with last-check labels at 320/390 px (`library-20261001-picker/`).
The first attempt (`checks-d60be5fb3b`) had 337 passes and one missing-target error in a
new test fixture; corrected and rerun, not skipped. The initial standalone unit check
hit sandbox temp-folder permissions; its external isolated rerun passed. One existing
Starlette/httpx deprecation warning remains.

Real Ollama: **one separate test passed** using synthetic structured facts on loopback,
including validated wording and persistence (`library-20261001-ollama/`). No device was
contacted by that test. Fresh installed package passed six pages, nine assets, demo
create/reopen and `pip check` (`package-03ce97abac/`). Dependencies were not changed.

Read-only archive review: **41 readable, zero unreadable normal reports**, JSON hashes
unchanged. Repeated history query returned identical results in 256.7 ms cold / 58.5 ms
warm, with 57 / 16 full-report reads; one observation, not a general speed guarantee.
See `.test-artifacts/library-20261001-review/results.json`.

**Live Light and Sony Deep tests were not run:** the active Wi-Fi was ANGLIA.LOCAL,
10.240.108.0/22, previously identified as unauthorised by the owner. The execution plan
retains the home-network gate and follow-up steps. Physical-device, Ubuntu and reader
evaluation remain pending; no new live results or human-study data are claimed.

## Report usability fixes - 30 September 2026, evening

Implemented the live-review fixes: unfinished-check headings now stack above their
notes; comparison cards show device addresses; name retries show visible pending,
reported-name, no-name and failure feedback beside the device; search is labelled
"Search devices and results". A UI-contract mismatch explains the required backend
restart before new setup, but existing-job recovery remains available. Module versions
are coordinated as `20260930-report-fixes`.

The full three-engine suite passed **328 Python and 45 JavaScript tests**, lint/format
and eight JavaScript syntax checks: `.test-artifacts/checks-c3b75f7dba/`. Responsive
coverage includes the existing 144 combinations plus six explicit unfinished-check
layouts (320/390 pixels in three engines). Library browser assertions cover comparison
identifiers and visible returned/empty/failed name outcomes. New JavaScript tests cover
an outdated backend and recovery of an existing job despite the version mismatch.

After hiding the initially empty name-feedback paragraph, the focused library browser
test passed again: `.test-artifacts/report-fixes-library-final/`. Its first invocation
failed before test execution because the parent temporary directory was missing;
created that directory and reran successfully. A reopened copy of the previous partial
live report confirmed the fixed mobile layout, visible no-name feedback, all nine
device cards, seven finding panels, history and Deep prefill without new scans.

Final installed-wheel verification passed six pages, nine assets, demo read/create/reopen
and dependency consistency: `.test-artifacts/package-da4b9b36d5/`. Security gates passed
with no known advisories, no medium/high static findings (12 reviewed low findings), and
no potential secrets: `.test-artifacts/security-fcf63d37ef/`. The existing Starlette/httpx
deprecation warning remains. Normal reports were not migrated or rewritten.

Pi-hole deployment/live testing is now deliberately deferred to the
[future-improvements section](evaluation.md#future-improvement-optional-pi-hole-naming).
The requested [Sony Deep scan](deep-sony-20260930.md) completed in 9m48s on its first
attempt: 15 open services, nine review items (two low, seven informational), ten validated
Ollama records and a fresh mDNS name. Evidence replay, real-report controls and Deep
Run again choices passed. All 41 normal reports remained unchanged; the report is saved
separately in `.test-artifacts/deep-sony-20260930-a/`. This is one device observation,
not a security certification or proof that all devices will advertise their names.

## Post-restart live recheck - 30 September 2026

The restarted normal backend now serves the current assets and registers the new
library routes; its authentication boundary remains intact. A fresh isolated live Light
run finished in 3m38s: nine discovered, eight checked, one unreachable after two attempts,
11 open services and seven review items. All eight Ollama records validated and preserved
incomplete coverage. The failed-device card and retry remain visible; this is not a
clean assessment of every device. All 41 normal saved reports were preserved.

Evidence replay, re-opened report controls and responsive views passed. A mobile warning
label still wraps awkwardly; prior comparison/name-feedback usability gaps also remain.
The checker encountered a transport interruption on one attempt and an incorrect card
count assertion on the next; both are retained, explained and distinguished from app
behaviour in [the full follow-up record](live-check-20260930.md#follow-up-after-the-backend-restart).
The corrected follow-up browser review did not start another port scan.

Regression: **328 Python and 43 JavaScript tests passed**, three-engine responsive
coverage, lint/format and syntax: `.test-artifacts/checks-7d49eacdee/`.
Security gates passed: `.test-artifacts/security-d9c34a31cd/` (12 reviewed low static
findings, none medium/high; no known dependency advisories or potential secrets).
Private live evidence: `.test-artifacts/live-acceptance-20260930-c/`.
No direct authenticated test of the normal instance, live Deep run or Pi-hole operation
is claimed; the normal instance's session link was unavailable to the checker.

## Live acceptance check - 30 September 2026

[Full live record and recommendations](live-check-20260930.md): the current code completed
one authorised home Light scan in 3m12s, with seven of seven discovered devices checked,
11 open services, seven review items and eight validated Ollama records. Refresh,
history, real name-only retries, the Deep picker, responsive live-report views and
evidence replay passed. All 41 normal reports validated and normal JSON hashes were
unchanged; the new report remains in the isolated test folder.

The full three-engine rerun passed **328 Python and 43 JavaScript tests**, lint/format
and eight JavaScript syntax checks: `.test-artifacts/checks-ed36d9a201/`.
Private live artifacts: `.test-artifacts/live-acceptance-20260930-a/`.

Important deployment finding: the existing server on port 8765 did not advertise the
new `/api/reports` route. It needs a backend restart; verification used a current-code
isolated instance, not a restart of the user's server. Only one fresh DNS name and one
historical name were available; no fresh mDNS names or Pi-hole operation were verified.
See the record for comparison-card/name-retry usability gaps and remaining Deep/lab work.

## Experience and discovery improvements - 30 September 2026

Implemented all seven steps in [the plan](experience-improvements-plan.md): unified
device/finding search, recent-Light choices for Deep setup, a per-job running overview,
filtered history and titles, cross-tab nickname updates, explicit bounded name-only
refresh and visible saved comparisons. Original scan evidence remains separate from
editable annotations. Optional title/name data failures leave results accessible with
a persistent notice; tests also cover corrupt optional data in history search.

Final `scripts/check.py --browser --browser-engines chromium,firefox,webkit` passed
**328 Python tests and 43 JavaScript tests**, Ruff lint/format (103 files) and syntax
checks for eight JavaScript modules. One live-provider test was deselected; one existing
Starlette/httpx deprecation warning remains. Artifacts: `.test-artifacts/checks-673082ad07/`.
An approval-service timeout initially prevented the final command from starting; the
allowed retry completed successfully. It was not a test failure.

Browser coverage includes the existing **144 page/size/engine combinations** across
Chromium, Firefox and WebKit, plus text-size, keyboard and selected touch checks. The
new synthetic library workflow verifies devices without findings, multiword search,
nickname changes across two tabs without losing selection, titles/history filtering,
picker prefill without an automatic scan, mocked later name claims, and readable
results when annotation retrieval fails. Unit tests verify search before pagination,
date/profile validation, scope/authorisation/CSRF, revision conflicts and preservation
of the original `scan.json` bytes.

Fresh installed-wheel verification passed six pages, nine static assets, demo read/
create/reopen and dependency consistency: `.test-artifacts/package-590708c835/`.
The earlier security gate passed with no known dependency advisories, zero medium/high
static findings (12 reviewed low findings retained), and zero potential secret alerts:
`.test-artifacts/security-085a0662c8/`. That gate preceded the final UI-only optional-data
notice regression; the final full browser/package checks include it.

No live Nmap scan, real name lookup, Ollama invocation, Pi-hole deployment, backend
restart or normal report migration was performed. Real-network DNS/mDNS behaviour,
Pi-hole extraction, Ubuntu execution, physical devices, reader-study outcomes and
large-archive search performance are not established by these checks. History search
currently reads saved JSON rather than using an index. Titles/name annotations are not
pushed across tabs; only nickname revisions are polled. Restart the backend when no
jobs are running, reopen its session link and hard-refresh to load the new routes/assets.

## Five-job default and quiet capacity waiting - 29 September 2026

Raised the config and supervisor default to five active scan jobs; explicit environment
overrides remain supported. Two Nmap process slots and serial AI preparation are unchanged.
Added admission availability to status. Full setup pages disable Scan with a neutral inline
message, poll availability every three seconds and re-enable without automatically submitting.
A competing HTTP 429 follows the same quiet path; other errors remain visible.

Final three-engine `scripts/check.py --browser --browser-engines chromium,firefox,webkit`
passed **319 Python and 42 JavaScript tests**, lint/format and seven JS syntax checks.
One live-provider test deselected, one existing Starlette/httpx warning. Artifacts:
`.test-artifacts/checks-085babaab4/`. The first attempt stopped on mixed line-ending format;
normalized the edited supervisor file before the successful full rerun.

Admission regressions verify both two- and five-job limits and rejection of the next job.
Browser regressions retain a two-job synthetic limit to exercise quiet waiting, cancellation,
re-enabling Scan and absence of automatic submission, through both direct pages and the old
shortcut. JavaScript covers a last-slot race separately. No five-job live-load/performance
claim is made. No normal reports were migrated and no running backend was restarted.
Restart after active work finishes to apply the new default; an existing environment override
such as APP_MAX_CONCURRENT_SCANS=2 must be changed explicitly if five slots are wanted.

## Dedicated Light and Deep pages - 29 September 2026

Added `/light` and `/deep` with fixed profiles using the existing dashboard template.
Direct pages share backend/nickname/settings/report storage but use profile-specific
pending keys and route-preserving UUID links. Opening Deep while Light runs leaves Deep
ready for explicit setup; it does not reconnect to Light. Mismatched pasted job links
open the general progress view rather than mislabelling the saved scan profile.

Final `scripts/check.py --browser --browser-engines chromium,firefox,webkit` passed:
**318 Python and 40 JavaScript tests**, lint/format and seven JavaScript syntax checks.
One live-provider test was deselected; the existing Starlette/httpx warning remains.
Artifacts: `.test-artifacts/checks-6318f373f8/`.

The concurrent-job browser test now covers both the existing new-tab shortcut and direct
Light/Deep URLs: simultaneous synthetic scanner activity, independent refresh, third-job
capacity rejection, isolated cancellation and separate saved outcomes. Responsive tests
cover six pages at eight sizes in three engines: **144 page/size/engine combinations**,
plus the existing text-size, keyboard and selected touch-emulation checks.

Fresh installed-wheel verification passed all six routes, eight assets, demo read/create/
reopen and dependency consistency: `.test-artifacts/package-4ae37b818a/`.
No live network scan, new model invocation, normal saved-data migration or backend restart
was performed. Nickname identity/reuse rules are unchanged; this change does not add live
push notifications for nickname edits in already-open reports. Restart the existing backend
when no scan is running to register the new routes, then use its session link.

## Restored layout and independent Light/Deep tabs - 29 September 2026

Restored first-action guidance to the Understanding your results card, below the summary,
as requested. Kept responsive/accessibility fixes and factual counts. Updated coordinated
asset versions so a cached dashboard does not hide the new controls.

Added explicit new-tab setup and per-job URL recovery to the existing shared API. The
synthetic browser regression runs Light and Deep simultaneously, reloads both tabs,
checks distinct job IDs, rejects a third job at the two-job limit, cancels only Deep,
then finishes Light and verifies separate saved outcomes. No real device is contacted.
JavaScript regressions cover copied tab storage, explicit job selection and cancellation.
Responsive regressions now require the restored guidance placement, not the earlier panel.

Final `scripts/check.py --browser --browser-engines chromium,firefox,webkit` passed:
**316 Python tests and 37 JavaScript tests**, Ruff lint/format and all seven JavaScript
syntax checks. One live-provider test was deselected and the existing Starlette/httpx
deprecation warning remains. Responsive matrix: three engines, eight sizes, four pages.
Artifacts: `.test-artifacts/checks-25ca5828d3/`.

The new browser fixture initially lacked a simulated detected network, then needed an
explicit reload after fragment-only setup navigation; corrected both fixture issues.
The focused concurrent-tab check and final full suite then passed. No scanner scope,
instance lock, backend admission limit, real report or model configuration was changed.
This verifies concurrency with synthetic scanner output, not concurrent live-network load.
Physical-device testing and live Ollama performance with queued jobs remain unverified.

## Usability, responsive and release-check follow-up - 29 September 2026

Implemented a first-action panel above report statistics, checked versus discovered/
selected counts, precise complete/partial/empty coverage wording, stable equal-priority
ordering, simpler feature/evidence labels and narrowly deduplicated guidance. Technical
details, original wording and AI provenance remain available; stored evidence is unchanged.

- Final isolated suite: **315 Python and 34 JavaScript tests passed**, Ruff lint/format
  and seven JavaScript syntax checks passed. One live-provider test was deselected;
  one Starlette/httpx deprecation warning remains. Artifacts:
  `.test-artifacts/checks-c0a9814a50/`.
- Responsive matrix: Chromium, Firefox and WebKit; eight sizes from 320x568 to 2560x1440;
  four pages, giving **96 engine/page/viewport combinations**. Checked overflow, long
  names, counts, first-action placement and dialogs. Additional checks cover keyboard
  focus, 200% root text size, and Chromium/WebKit touch navigation without starting scans.
  These are emulations, not physical-device or full accessibility certification.
- Fresh-wheel installation passed for all four pages, eight static assets and saved-demo
  create/reopen, plus dependency consistency: `.test-artifacts/package-ee645f08a2/`.
- Final security gate passed: no known dependency advisories, zero remaining secret
  alerts, zero medium/high static findings. Twelve low findings are reviewed in
  [release checks](release-checks.md). Artifacts: `.test-artifacts/security-650c28bac1/`.
  The separate security-tool lock audit also passed: `.test-artifacts/security-tools-audit.json`.
- Copied real-report recovery drill passed: 12 devices/eight findings retained from the
  previous checkpoint. Its incomplete state remained explicit; source and copied evidence
  hashes were unchanged. Artifacts: `.test-artifacts/restore-ayca79h7/drill.json`.
- Reopened a copy of the last real report with the updated interface at desktop/mobile
  sizes. All eight finding panels and 12 device cards/rows remained accessible, nine saved
  explanation records validated, refresh worked, and no page overflow/browser errors
  occurred. Artifacts: `.test-artifacts/responsive-saved-20260929/`. This was not a fresh
  scan or new Ollama invocation. All 34 normal saved reports retained their prior hashes.

Failures retained in the work record: coordinated asset-version assertions first needed
updating; the added restore regression initially omitted its synthetic target and failed
schema validation (`checks-f54f13bdb4`). Corrected the test fixture, then reran the whole
suite successfully. The first dependency audit found two entries for one pytest advisory;
patched test dependencies in an isolated environment and reran the audit. Five narrowly
reviewed synthetic/password-file-reference secret alerts have exact-line comments, not
broad exclusions. Runtime dependency pins were not changed.

No new live scan, backend restart, router change, Pi-hole installation, commit or push
was performed. Remote Ubuntu CI/protection enforcement, physical phones/tablets, actual
Pi-hole/ground-truth Deep evaluation and a real nontechnical-reader study remain pending.
Commands and remaining limitations: [repeatable release checks](release-checks.md).

## Standards-informed quality baseline - 28 September 2026, evening

Created the [quality plan](quality-plan.md) and [requirements matrix](quality-traceability.md)
before a new authorised home Light run. [Full measured record](quality-evidence-20260928.md):
4m15s, 14 discovered, 13 checked, one unreachable after two attempts, 13 open services,
eight review items and nine validated Ollama records. Three current device names came
from mDNS/reverse DNS, not Pi-hole. All facts/findings replayed from retained evidence.

306 Python and 31 JavaScript tests, browser workflow, lint/format/syntax and fresh-wheel
checks passed. Actual live-report desktop/mobile review passed. All 34 normal reports
validated and their pre/post hashes match. No application source was changed or deleted;
documentation now records quality gates, organisation recommendations and usability work.
Actual Pi-hole, Ubuntu/remote CI, ground-truth Deep and reader-study results remain pending.

## Dashboard startup/cache regression - 28 September 2026

The running app served current assets and a clean browser reached the session-expiry
message with Retry connection enabled. Supplying the previous `report.mjs` reproduced
the user's exact stuck state: missing `readScanSetup` export, "Checking scanner..."
and a disabled button. This demonstrates a cached-module failure path, not direct
inspection of the user's browser cache.

- Versioned page scripts and their imports together to bypass old cached modules.
- Added `Cache-Control: no-store` to local responses and no-store browser API fetches.
  Restart the backend to activate the new response middleware.
- Added an independent dashboard startup guard that shows a Reload page action if a
  module fails. The same stale-module reproduction now leaves the button usable.
- Browser API/session requests time out after 20 seconds and do not retry writes
  automatically; the message warns that an already requested scan may still be running.
- Full `scripts/check.py --browser`: **306 Python tests and 31 JavaScript tests passed**,
  plus syntax/lint/format. Artifacts: `.test-artifacts/checks-393e5740e6/`.
  Browser regression deliberately supplies a broken module, checks the recovery button,
  reloads successfully, and confirms no scan starts during this sequence.

No live scan, credential change, saved-report edit or running-backend restart was done.
Hard-refresh the page with Ctrl+F5; after restarting the backend, use its current session
link if the old session has expired. Existing dependency deprecations remain visible.

## Run again navigation - 28 September 2026

- `.venv-brief/Scripts/python.exe scripts/check.py --browser` passed **305 Python
  tests and 29 JavaScript tests**, seven syntax checks and Ruff lint/format.
  Artifacts: `.test-artifacts/checks-f2139b678a/`. No live provider or network scan ran.
- Light Run again opens dashboard setup; known-host lists are retained visibly, with
  an option to use the local network instead. Deep opens an accessible native dialog:
  same address, another address, or cancel. Nothing is submitted until Scan is pressed.
- Browser checks cover Cancel/Escape, same-address prefill and refresh, empty-address
  validation, existing report preservation, and no new scan on navigation. Unit tests
  cover bounded setup data, stale tab storage and resuming a genuinely active job.
- After the final progress-notice adjustment, dashboard tests and a focused browser
  rerun passed. The mobile dialog screenshot was inspected without page overflow:
  `.test-artifacts/rescan-browser-20260928/`.
- Pi-hole is still not deployed. Docker is absent from PATH/normal install locations;
  WSL reports not installed. Host selection and administration access are needed before
  configuration can continue. No Windows features, DNS or router settings were changed.

## Live verification - 28 September 2026

One new authorised home Light scan completed its workflow in 3m35s: nine completed
device checks, one unreachable device, eleven open services and seven review items.
Ollama processed all eight records in two requests, with no rejected fields; two
records retained original wording. Saved progress reached 8/8. Actual desktop/mobile
report review, refresh and retained-evidence replay passed. All 32 normal saved reports
validated read-only. The offline rerun passed 304 Python and 24 JavaScript tests.
See [live results and remaining evaluation work](live-check-20260928.md).

## Fixes and usability improvements verified - 27 September 2026

Final command: `.venv-brief/Scripts/python.exe scripts/check.py --browser --ollama`.
Artifacts: `.test-artifacts/checks-cf166d0d36/`.

- **306 Python tests passed**: 304 offline, one real Edge workflow using synthetic
  scanner/provider responses, and one real local-Ollama test using synthetic facts.
- **24 JavaScript tests passed**, plus seven JavaScript syntax checks and Ruff
  lint/format (92 Python files). The runner now includes the shared API-client tests.
- New regressions cover structured validation messages, blocked browser storage,
  stale/missing AI records, unreachable hosts in both profiles, bounded storage locks,
  unchanged evidence, plain report projections, and persisted AI batch counts/cache reuse.
  The browser verifies refresh during AI preparation and the new feature labels.
- Fresh installed wheel passed dependencies, four pages, eight assets and demo
  create/read/reopen: `.test-artifacts/package-f877ed050f/`.
- Reopened the previous isolated home report in Edge at desktop/mobile sizes: nine
  saved wording records validated, all finding panels opened, refresh passed, no
  JS/HTTP errors or page overflow. Its saved scan hash is unchanged. Read-only report
  display now consistently uses reviewed plain-language choices and shows safe
  address-bar instructions for confirmed web services. Artifacts remain under
  `.test-artifacts/live-review-cnxvbgno/` (`review.json` and screenshots).
- Replayed eleven retained host results and reproduced all eight findings. Replaying
  the two retained zero-host results now raises `HostUnreachable`, not generic invalid
  output. Historical report reason codes were not rewritten.
- All **30 production reports** still validate, none changed; largest 179,875 bytes.

The first full pass found a browser assertion expecting the old capitalised outage
message; it was updated to the explicit AI-outage message and the final full run passed.
Existing dependency deprecations remain (1,091 warnings); they are not test failures.
No new network scan, Pi-hole installation, production-data migration, commit/push or
running-backend restart was performed. Actual Pi-hole, controlled live Deep, Ubuntu/CI
and nontechnical-reader evaluation remain pending. Older entries below are historical;
their three readability/classification follow-ups are now implemented.

## End-to-end architecture and organisation check - 27 September 2026

Final command: `.venv-brief/Scripts/python.exe scripts/check.py --browser --ollama`,
with pytest coverage enabled through `PYTEST_ADDOPTS` and an isolated coverage file.

- **290 Python tests and 18 JavaScript tests passed**, seven JavaScript syntax checks,
  Ruff lint/format (90 Python files). Run: `.test-artifacts/checks-c8915fa3eb/`.
- **88% Python statement coverage** (2,920/3,301 statements). Storage 92%, supervisor
  89%, AI orchestration 92%, pure validator 81%, scan/settings APIs 71%. Coverage
  identifies testing gaps, not a reliability score. JSON report:
  `.test-artifacts/end-to-end-20260927/final-coverage.json`.
- The browser check uses synthetic Light/Deep observations and provider failures;
  the separate local-Ollama test uses synthetic facts. Refresh, saved history,
  rejected wording/retry, nickname edit/removal and expired-session paths remain covered.
- The previous real report reopened in Edge at desktop/mobile sizes: nine wording
  records validated, all finding panels opened, refresh passed, no JS/HTTP errors
  or page overflow, saved scan hash unchanged. Replaying its eleven retained Nmap
  host results reproduced all eight findings. This is replay, not a fresh scan.
- All **30 production reports** read successfully without changes (largest 179,875 bytes).
- Fresh installed wheel: dependencies, four pages, eight assets, demo create/read/reopen
  passed; includes the extracted validator. `.test-artifacts/package-6f975c7a34/`.
- The `.venv` used by VS Code passes `pip check` and `python -m app doctor`, reporting
  Nmap 7.991 and a configured AI provider. Real model availability was tested separately.

Organisation only: extracted 155 lines of pure validation from the AI service; compared
the function body unchanged after dedenting/renaming. New tests check the existing
service entry point delegates to that validator and all substantive application modules
are import-reachable. All shipped HTML/JS/CSS remains referenced. No source, reports,
virtual environments or user task changes were removed.

The three known follow-ups from the live review remain open, as do actual Pi-hole,
controlled live Deep/lab, Ubuntu/remote CI and nontechnical-reader evaluation. Existing
Starlette/httpx and pytest-asyncio deprecations remain (1,019 warnings in the final run).
No new network scan, commit, push or running-backend restart was performed.

## Final regression recheck - 27 September 2026

- Full runner with `--browser --ollama`: **288 Python tests and 18 JavaScript tests
  passed**, plus seven JavaScript syntax checks and Ruff lint/format (88 Python files).
  Artifacts: `.test-artifacts/checks-0ea1be58d7/`. Existing dependency deprecations
  remain visible (1,019 warnings); no test failures.
- Fresh installed wheel passed dependency consistency, four pages, eight static
  assets and demo create/read/reopen: `.test-artifacts/package-0061941096/`.
- The actual `.venv` referenced by VS Code tasks imports the app, passes `pip check`,
  and resolves Nmap 7.991. `tasks.json` parses; its current edit is formatting-only.
- Read-only audit: all **30 saved reports** validate, none were changed, largest
  179,875 bytes. The two most recent completed reports have ready AI, two requests
  each and zero rejected fields; the intervening report was cancelled, not failed.
- Replayed the previous isolated live scan: eleven host results and all eight
  findings still match retained evidence. No new network scan was run.

The three follow-ups in `live-check-20260926.md` remain unfixed: classify zero-host
Nmap output separately from invalid data, consistently prefer beginner wording, and
give usable instructions for opening a device page/understanding feature counts.
Real Pi-hole, Ubuntu/remote CI and participant comprehension remain unverified.
No application code, user task edits, running backend or saved reports were changed.

## Beginner-report brief implementation verification — 26 September 2026

- `.venv-brief/Scripts/python.exe scripts/check.py --browser --ollama`: **288 Python
  tests passed** (286 offline, one Edge workflow, one local Ollama synthetic-facts test),
  **18 JavaScript tests**, seven JS syntax checks, Ruff lint and formatting (88 Python
  files). Artifacts: `.test-artifacts/checks-f172d9877d/`.
- New regressions cover partial-field retry across requests, preserved accepted list
  elements, constrained output shape, nickname edit/removal/revision conflicts, no
  IP-only reuse, scope/age/future/duplicate-MAC safeguards, corrupt annotations leaving
  reports accessible, request boundaries, neutral counts and readable check labels.
- Edge exercised nickname creation with literal `<script>` text, reload and removal,
  both scan profiles, AI outage/retry and existing progress/session flows. PUT now
  participates in both the server Origin/CSRF boundary and browser header handling.
- Real `llama3.2:3b`, disposable copy of the latest report: **16 rejected fields → 0**,
  **two additional requests**, ready status, every previously accepted field preserved,
  original scan file hash unchanged and devices/services/findings/coverage identical.
  Artifacts: `.test-artifacts/brief-ai-719a1wph/verification.json`.
- That copy was reopened in Edge at 1440 px and 390 px: eight wording records validated
  against approved choices, all finding panels opened, refresh passed, no JS/HTTP errors
  or page-level horizontal overflow, saved report unchanged. Screenshots and extracted
  text are under `.test-artifacts/brief-ai-719a1wph/`; they contain private identifiers.
- Fresh wheel/runtime-lock installation passed `pip check`, four pages, **eight assets**,
  and demo create/read/reopen. Artifacts: `.test-artifacts/package-9a975d7b43/`.

During development the old output shape still allowed wrong action ordering and the
first stricter schema used a boolean keyword unsupported by the local provider. The
final schema uses compatible object forms plus exact ordered choices for short lists;
the application still independently validates all output. The live-provider test now
allows the documented one bounded retry, while requiring ready status, no rejected
fields and validated wording. No factual validation was weakened to pass tests.

Existing Starlette/httpx and pytest-asyncio/Python 3.14 deprecation warnings remain.
No new live network scan was run. Existing user reports and the running backend were
not modified. This is software and wording verification, not a completed human study.

## Live scan followed by full checks — 26 September 2026

See [the live evidence and beginner-readability review](live-check-20260926.md).
One authorised home Light scan completed all ten discovered host checks, recorded
11 open services and seven review items (three low, four informational), and prepared
AI explanations in two requests. The full suite then passed: **276 Python tests and
17 JavaScript tests**, browser/local-Ollama checks, lint, formatting and syntax checks.
Fresh installed-wheel verification passed; all 27 existing reports read successfully.

The review found a confirmed AI retry gap: partially accepted records are cached as
ready, so another preparation request does not retry their rejected fields. Sixteen
fields retained original text in this scan. Other follow-ups concern the count-based
red ring, exposed internal field names, repetitive/generic actions and unknown-device
recognition. No application-code fix was made in this checks-only turn.

## Progress, device summaries and AI retry follow-through - 26 September 2026

Final command: `.venv-brief/Scripts/python.exe scripts/check.py --browser --ollama`.

- **274 offline Python tests passed.** New cases cover persisted enrichment progress,
  targeted AI retry, continuation after an invalid batch and sanitised parser diagnostics.
- **1 real Edge workflow passed** with synthetic scanner/provider responses, including
  refresh while gathering details, refresh during AI, device cards, saved history,
  AI outage/retry, expired sessions, and Light/Deep report paths.
- **1 real local Ollama test passed**, using synthetic facts; not a live network scan.
- **17 JavaScript tests**, six syntax checks, Ruff lint and formatting passed (83 Python
  files). Full-run artifacts: `.test-artifacts/checks-5b11c7ad2b/`.
- `scripts/check_package.py` built a wheel, installed it with all runtime lock pins in
  a fresh Windows/Python 3.14 environment, passed `pip check`, and served four pages,
  seven assets and demo create/read/reopen from the installed package. Artifacts:
  `.test-artifacts/package-11d81b4818/`. A subsequent parser change only wrapped long
  diagnostic string literals for lint; final source tests above cover that change.

The initial sandboxed test invocation failed because Windows denied access to its
temporary test directory. The approved isolated reruns passed; no production data or
permissions were changed to bypass this. Existing Starlette/httpx and pytest-asyncio/
Python 3.14 deprecation warnings remain visible.

Prepared `.github/workflows/checks.yml` for Windows/Ubuntu, Python 3.12/3.14, synthetic
browser checks and fresh-wheel verification. Action commit pins were resolved from
official GitHub repositories. It was not committed, pushed or run remotely; Ubuntu
compatibility is not yet established. The reader-study session kit and empty results
template are prepared, not completed participant research.

No live network scan, Pi-hole request or rewrite of existing user reports was performed.
The previous `HOST_RESULT_INVALID` live failure lacks retained XML; the exact cause is
still unknown. New failures now preserve reviewed diagnostic detail instead of only
the broad invalid-output category. Restart the normal backend to load these changes.

## Review fixes - 26 September 2026

Fixed three issues found during code review:

- Light scan parsing now retains explicit protocol/port states from Nmap
  `extraports` summaries. Closed summaries establish a response; ambiguous,
  malformed or out-of-profile entries do not. Deep scans retain response evidence
  without expanding bulk non-open summaries into thousands of service records.
- Discovery passes its candidate addresses to mDNS before the eight-host cap and
  filters saved announcements to the requested target range. A synthetic /30
  scan within a busy /24 exercises the complete supervisor/browser path.
- HTTP guidance now points to any recorded optional redirect check and explains
  its root-page limitation. It no longer asserts that redirection was never tested.
  Rule R03 is 1.1.1, the ruleset is 1.2.1, and reviewed-wording cache version is
  4.2.1. Existing reports can receive the correction through explicit guidance refresh.

Verification: `.venv-brief/Scripts/python.exe scripts/check.py` passed **270 Python
tests** (18 added regression cases), **16 JavaScript tests**, six JavaScript syntax
checks, Ruff lint and formatting. Artifacts: `.test-artifacts/checks-9db3732d5a/`.
Existing Starlette and pytest-asyncio deprecation warnings remain. Tests used
isolated data; no saved user reports were changed. No live network scan, real
browser workflow or live Ollama check was run for these fixes.

## mDNS name reliability and authorised home scan - 25 September 2026

The two latest user reports both contained 11 device results, but names fell from
three to two. The missing TV name had the same recorded MAC in both reports; its
AirPlay/Google Cast announcements were absent in the later report. All announcements
that were collected had been assigned names, and neither mDNS cap was reached. This
establishes missing observations, not that the new classification rules erased names.
Serial 300 ms lookups in a short discovery window were a plausible reliability weakness,
not a proven explanation for the TV's silence.

Implemented nonblocking mDNS lookup workers, a four-second collection window and one
retry per service; explicit friendly-name/hostname fallbacks; RAOP display-prefix cleanup;
and visibly historical names from recent direct observations matched by scope/MAC.
Historical labels cannot override fresh names, extend their own age, imply reachability,
or strengthen device classification. Conflicting prior labels stay marked as conflicting.

Verification before scanning: **254 Python tests passed** (252 offline, real Edge with
synthetic scans, and real local Ollama with synthetic facts), **16 JavaScript tests**,
six JS syntax checks and Ruff lint/format passed. Artifacts:
`.test-artifacts/checks-168224e841/`. Additional historical-label assertions subsequently
passed in the report JavaScript suite. New regressions cover mDNS retry/concurrency,
cancellation cleanup, name preference, stale/future/cross-network/duplicate/IP-reuse
rejection, fresh-name precedence and preservation of historical conflicts.

The user explicitly requested a live scan. Active Wi-Fi was confirmed inside the saved
home range before starting one **Light** scan through the authenticated application API.
The currently open app and its data folder were left untouched. The check used isolated
storage with copies of recent same-scope reports to exercise historical-name fallback.

| Live result | Observation |
| --- | --- |
| Discovered devices | 10 |
| Completed device checks | 9 |
| Unfinished device checks | 1; invalid Nmap host result after two attempts |
| Confirmed open services | 11 |
| Findings | 7: three low, four informational |
| Current name sources | 1 mDNS, 1 reverse DNS |
| Historical name | Sony TV restored with same-MAC match, historical label and prior conflict |
| Total named devices | 3; **only two were current name observations** |
| Fresh mDNS advertisements | 2, from one device; no fresh TV advertisement |
| AI | Initially six findings plus overview ready; one response invalid. Saved-evidence retry completed all seven findings and overview with one additional request. Evidence unchanged. |
| Real browser | Historical label/provenance, unfinished-check disclosure, refresh and no JS errors passed |

This is a **partial scan**, not a claim that every device was checked. The naming
workaround worked, but the live run does not prove increased fresh mDNS response rate.
The unfinished host check and occasional invalid Ollama response remain follow-up issues.
No Pi-hole installation/query, Deep scan, wider network or packet capture was involved.

Private local artifacts: `.test-artifacts/live-names-kwlhe1ul/`; report ID
`78093192-6934-4e7d-890a-41e70cfd803f`; screenshots `report.png` and `historical-name.png`.
These remain outside Git and the normal app history. Restart the normal backend before
using the updated naming code for a new scan. Existing reports were not rewritten.

## Follow-up fault review and organisation - 25 September 2026

Final `python scripts/check.py --browser --ollama`: **240 Python tests passed**
(238 offline, one real Edge synthetic-network workflow, one real local Ollama test
with synthetic facts). **16 JavaScript tests**, all six JS syntax checks, Ruff lint
and formatting passed. Artifacts: `.test-artifacts/checks-ce405808ea/`.

Eight new regression cases first reproduced four defects, then passed after fixes:

- Empty, whitespace and placeholder UPnP fields raised `TypeError`, aborting later
  optional details. Empty values are now skipped without dropping valid model metadata.
- Missing saved port selections compared equal and allowed unjustified service-history
  comparisons. Both reports must now contain explicit port-selection lists.
- Optional collection errors also acquired a timeout/cancellation explanation and
  prevented the next independent lookup. Errors, unfinished work and successful sources
  are now kept distinct; a failing web collector does not suppress computer-name lookup.
- Port-table guesses or unknown service identification counted as confirmed device-type
  evidence. Only probed open-service names now strengthen a type suggestion.

Organisation: extracted optional scheduling/checkpointing to `app/jobs/enrichment.py`
and pure observation formatting to `app/scanner/observations.py`. History no longer
imports the HTTP collector to format text. The import-reference audit inspected 44
application modules and found no unreached non-initialiser module. The asset traversal
test covers every shipped stylesheet/script. No source files were deleted.

A fresh wheel under `.test-artifacts/review-enrichment-package/` was installed only in
`.venv-package`. Explicit imports of the reorganised modules, four pages, seven static
assets, demo read/create/reopen and `pip check` passed. The final verification helper
was also checked after adding those import assertions.

Read-only configured-storage check: **25 readable reports** (15 completed, six partial,
three failed, one cancelled), no device/report ownership mismatches, and referenced
guidance files readable. No report was rewritten, reconciled, recovered or deleted.
This confirms file consistency, not the truth of historical network observations.

No live network scan or Pi-hole query was run. Live richer-collector/Deep interoperability,
real Pi-hole, Ubuntu and reader-study checks remain separate work. Existing Starlette
test-client and pytest-asyncio/Python 3.14 deprecation warnings remain visible.

## Richer device details - 25 September 2026

- `python scripts/check.py --browser --ollama`: **232 Python tests passed** (230
  offline tests, one real Edge workflow using synthetic network/provider responses,
  and one real local Ollama test using synthetic facts). **16 JavaScript tests**, all
  six module syntax checks, Ruff lint and formatting passed. Artifacts are under
  `.test-artifacts/checks-fe214bc8c8/`; real device addresses were not probed.
- Both Light and Deep are covered by authenticated API policy tests, known-host mDNS
  filtering/enrichment tests and the browser workflow. Browser checks verify the new
  expandable details, provenance wording, and safe text rendering of markup-like values.
- Collector tests cover TXT allowlisting, UPnP identity-only extraction, oversized/
  malformed/entity XML rejection, blocked external URLs, bounded same-device redirects,
  certificate-verification failure, selective NetBIOS name-only storage, conservative
  classification/history, legacy JSON loading, deduplication and explicit detail limits.
- Timeout/cancellation tests verify that optional extras do not discard completed Nmap
  evidence and leave no active collector tasks. Extra collector concurrency is capped
  at two. The older host-worker test now uses an explicit overlap event rather than a
  timing-sensitive sleep; it still requires exactly two concurrent workers.
- A fresh wheel in `.test-artifacts/richer-device-package/` was installed only into
  `.venv-package`. Installed-package verification passed: four pages, seven static assets,
  and demo read/create/reopen. `pip check` passed. Saved app reports were not modified.
- Existing Python 3.14/pytest-asyncio and Starlette test-client deprecation warnings
  remain. The earlier full run exposed two outdated mDNS test doubles; those fixtures
  were updated and the entire suite rerun successfully, not excluded.

These checks do **not** establish live interoperability of the new enrichment with
home devices, actual TLS servers, a Pi-hole instance, or Ubuntu. No new network scan
or Pi-hole installation was performed. The live-home entry below predates these changes.

## Home live verification — 25 September 2026

See [the live-check report](live-check-20260925.md) for the latest results: 12 home devices
completed Light checks, 13 open services, 8 review items, and completed local Ollama
preparation. Real report refresh/history/Settings checks passed. Python: 200 passed and
one timing-sensitive failure that passed on rerun; JavaScript: 16 passed. Updated-runtime
wheel checks passed. Real Pi-hole extraction is blocked by absent configuration/instance;
Deep needs a selected target. Earlier "not tested" entries below record the prior stage.

## Pi-hole setup changes — not tested (25 September 2026)

At the user's request, no tests or scans were executed for the latest Pi-hole deployment,
password-file configuration, Settings/VS Code changes or dependency-pin updates. The
new `tests/unit/test_pihole_setup.py` cases are written, not run. No Docker/Compose service
was started, no network settings were changed, and no existing reports were reprocessed.
The results below apply to the preceding revision, not these changes. Resume with the
[deferred acceptance checklist](pihole-setup.md#deferred-acceptance-checklist).

## Full code/workspace recheck - 25 September 2026

Latest verification, after organisation and additional storage fixes:

- `python scripts/check.py --browser --ollama`: **187 Python tests passed** (185 offline,
  real Edge with synthetic scanner/provider, and real local Ollama with synthetic facts).
  **16 JavaScript tests**, all six module syntax checks, complete Ruff lint and formatting
  also passed. Artifacts: `.test-artifacts/checks-bc77e5df3d/`.
- A fresh wheel under `.test-artifacts/package-recheck/` was installed in `.venv-package`.
  Installed-package checks passed for four pages, seven static assets and demo read/create/
  reopen; `pip check` passed. No app runtime data was used by these checks.
- Read-only data validation: 23 configured reports and 63 historical preview reports were
  readable, referenced guidance was readable, and device/report IDs matched. No existing
  report was updated, recovered or deleted. Historical preview queued/running records were
  not treated as live jobs.
- Added regressions for invalid JSON roots/non-finite numbers, corrupt cache fallback,
  recovered-device ownership and pure network scope selection without repeated OS commands.
- Existing pytest-asyncio/Python 3.14 and Starlette test-client deprecation warnings remain;
  they were reported, not suppressed or represented as runtime errors.

See [architecture](architecture.md) and [workspace organisation](workspace.md) for the
current map, cleanup archive and limitations. No current-network scanning was performed;
actual Pi-hole, home-network, Ubuntu and participant checks remain outstanding.

Older output directories referenced below were archived during cleanup; their dated
records are historical and their original contents can be recovered from the cleanup ZIP.

## Architecture fixes verification - 25 September 2026

- Offline Python: **170 passed**, two opt-in tests deselected; **86% statement coverage**.
  Isolated `.pytest-fixes-final07` storage; no existing saved reports changed.
- JavaScript: **16 passed** across dashboard, report and Live Server bridge suites.
- Real Edge and local Ollama: **2 passed**, using `.pytest-fixes-final-browser07`.
  Browser scans/provider responses are synthetic. The Ollama test calls only the local
  `llama3.2:3b` model and now requires accepted, changed plain-language meaning in both
  the overview and finding, plus unchanged original severity and actions.
- Final combined rerun after the visual wording correction: **172 passed** in
  `.pytest-fixes-handoff08` (170 offline plus browser and local Ollama). The correction
  avoids telling readers to look for unfinished checks on a fully completed report.
- Full `ruff check app tests scripts` and `ruff format --check app tests scripts`: passed.
  `pip check` passed in both development/runtime environments; Git whitespace checks passed.
- Fresh wheel built into `.pytest-fixes-final-wheel07`, installed in `.venv-package`,
  and checked with `python -I scripts/verify_package.py`: **four pages, seven static
  assets, demo catalogue read, demo create and reopen passed**. This fixes the missing
  packaged `app/demo/findings.json` found by the preceding audit.
- The final template was rebuilt/reinstalled from `.pytest-fixes-handoff-wheel08`;
  the same package verification passed again.
- New regressions cover default-route selection on Windows/Linux, shared-network scope
  mismatch rejection, authenticated lightweight polling, bounded host concurrency and
  time budget, final status at the JSON size cap, repeated terminal updates, partial
  Pi-hole failures, discovery identity through Pi-hole matching, naming/classification,
  AI field-level rejection audit, and non-destructive previous-checkpoint recovery.

No live Nmap, mDNS, DNS or Pi-hole network check was performed. The user confirmed the
current shared network is not authorised; live testing is explicitly deferred until
home. Real Pi-hole API compatibility, Ubuntu lab behaviour and comprehension by actual
nontechnical participants are **not** established by these synthetic tests.

Run the complete offline checks with:

```powershell
python -m pytest -m "not live_lab and not live_provider and not browser" --basetemp <fresh-folder>
node tests/dashboard_ui.test.mjs
node tests/report_ui.test.mjs
node tests/live_server_bridge.test.mjs
python -m ruff check app tests scripts
python -m ruff format --check app tests scripts
```

Earlier dated results below are historical, not the current test count or network scope.

## Implementation brief verification — 24 September 2026

Implemented automatic AI report preparation, the JSON write-size boundary and guidance
archives, failed-report access, known-host rescans, longer technical evidence, precise
mDNS status, saved history, bounded host retries, name provenance and optional Pi-hole.
See [implementation status](implementation-status.md) for all eleven items and remaining work.

Verification uses new temporary data folders and isolated Python environments:

- Offline Python regression suite: **143 passed**, two opt-in tests deselected.
- JavaScript report and Live Server suites: **9 passed**. All six JavaScript modules
  passed syntax checks; Ruff's `F` checks passed for application code.
- Real local Ollama, `llama3.2:3b`: **1 passed** with a synthetic report. Its analysis
  status was `ready`; the saved overview and finding wording were inspected. This is
  model integration evidence, not a completed human comprehension study.
- The final overview wording was rechecked with local Ollama alongside nine focused
  workflow cases: **10 passed**. A subsequent offline regression also covers cancellation
  before an AI task starts, preventing a report from remaining stuck in analysis.
- Real headless Microsoft Edge: **1 passed** with synthetic Nmap/provider responses.
  Verified dashboard waits through analysis, report display, history reopen, Light
  known-host rescan, factual results during an AI outage and AI retry without rescanning.
- Dependency lock installation and `pip check`: passed in isolated environments.
- Wheel built and installed in a clean runtime environment. Importing with Python `-I`
  confirmed the installed package served **four pages and seven static assets**.

The Windows sandbox still denies pytest temporary-folder access; the successful runs
used the approved test runner outside that sandbox with fresh, dedicated folders.
Warnings include Python 3.14/pytest-asyncio deprecations and the installed Starlette
TestClient's HTTP client deprecation. They did not fail verification.

Commands from the project root (replace temporary paths with new unused folders):

```powershell
python -m pytest -m "not live_lab and not live_provider and not browser" --basetemp <fresh-folder>
node tests/report_ui.test.mjs
node tests/live_server_bridge.test.mjs
$env:RUN_LIVE_OLLAMA = "1"
python -m pytest tests/live_provider_test_ollama.py --basetemp <another-fresh-folder>
$env:RUN_BROWSER_TESTS = "1"
python -m pytest tests/browser_test_workflow.py --basetemp <browser-fresh-folder>
python -m build --wheel
# After installing the wheel in a clean environment:
python -I scripts/verify_package.py
```

Not yet verified against a real Pi-hole instance or an authorised live network in this
session. The saved scope was `192.168.0.0/24`, while detection reported `192.168.91.0/24`;
the live target is awaiting confirmation. Ubuntu/WSL is not installed on this machine.
The Ubuntu lab and nontechnical-reader study remain pending; their protocols are in
[evaluation instructions](evaluation.md). Existing saved scans were not modified.

Earlier verification history follows; descriptions of optional AI below are historical.

## Source cleanup — 23 September 2026

Removed the unused standalone prototype, orphaned styles, uncalled backend stubs,
and unused OpenAI SDK dependency. Kept the active templates, module imports, demo
APIs, local JSON persistence, and VS Code Live Server bridge.

Verification after cleanup:

- Offline Python suite: **118 passed**, 1 live-provider test deselected.
- Report-renderer tests: **7 passed**; Live Server bridge tests: **2 passed**.
- All five JavaScript modules passed `node --check`.
- A new integration check renders all three pages, follows their module imports,
  and verifies that every remaining static asset is served and reachable.
- Regression tests cover all six service-to-rule mappings and encrypted-service exclusions.

Tests used isolated temporary JSON folders; existing saved scans were not modified.
No live network scan or Ollama request was made. A real-browser visual review was
not repeated for this cleanup. The local pre-cleanup source archive is
`.cleanup-backup-20260923-182505.zip`; the original prototype also remains in Git
checkpoint `b9c3242`. Historical verification notes below describe earlier work.

## Result honesty and readability review — 23 September 2026

The implementation now covers the reproduced FTP claim drift and polarity reversal,
unreviewed/cosmetic rewrites, identified services without a dedicated risk rule, priority
ordering, incomplete scan wording, HTTPS service labels, old AI records, and explicit
saved-guidance refresh. Refresh requires a session, CSRF token, matching revision, and an
idle report. It preserves evidence/ratings/dates and archives prior guidance in local JSON.

Verification commands (use a short, unique Windows temporary path for pytest):

```powershell
$env:RUN_LIVE_OLLAMA = "1"
.\.venv\Scripts\python.exe -m pytest --basetemp <new-short-temp-path> -m "not live_lab" --disable-warnings
node tests/report_ui.test.mjs
```

The full Python suite passed with 106 tests including local Ollama. The JavaScript suite
exercises the page renderer with a minimal DOM as well as its pure reporting functions;
it does not replace a real-browser or nontechnical-user study. A separate seven-finding
check against local `llama3.2:3b` accepted reviewed wording for six findings and retained
original guidance for one. No new home-network scan was needed. Readability is an editorial
assessment; the application no longer treats an arbitrary changed sentence as proof that
it is simpler. Ruff is not installed in the current virtual environment.

Earlier verification history follows.

Verified in the current Windows development environment:

```text
python -m pytest -q
95 passed, 1 skipped

$env:RUN_LIVE_OLLAMA = "1"
python -m pytest
96 passed with the synthetic local Ollama check enabled

python -m app --help
python -m app doctor
completed successfully
```

The default suite now collects unit, integration, security-boundary, supervisor-recovery, and JSON-concurrency tests. Dashboard integration checks also pass: all four JavaScript modules pass `node --check`, `GET /` returns 200 from a different working directory, and `GET /api/demo-findings` returns 8 labelled demo findings. Full browser automation, the evaluation harness, and packaging handover remain to be implemented.

The local AI explanation service is covered by offline tests for allow-listed input, loopback-only access, schema-constrained responses, response validation, rejection of invented security concepts, persistence, caching, disabled operation, and fixed-guidance fallback. AI analysis now runs after deterministic scan completion and cannot hold the completed scan result open. Optional AI wording now covers titles, explanations, limitations, recommended steps, and how-to-check lines; each accepted line is tracked, while original rule-based wording stays available. Larger reports are batched at six findings per request and optional AI work is capped at 24 findings per scan.

The latest suite also covers opt-in mDNS scope filtering and the eight-host cap, chronological JSON history summaries, storage permission probing, setting clear/rejection paths, analysis-stage restart recovery, per-line AI qualifier and scan-limitation preservation, action safety checks, bounded AI batching, explicit saved-report rewording without Nmap, CSRF, and short retries for transient Windows file locks. On this Windows host, pytest's normal temporary directory was inaccessible under the sandbox; the suite passed with an approved run using a dedicated temporary directory. No new live network scan or passive capture was run for these changes.

Ollama 0.34.2 and `llama3.2:3b` were exercised through the opt-in live-provider test. The contract accepts a validated rewrite or a deterministic fallback when the small model broadens the verified claim; severity and recommended actions remain unchanged. The live check passed with:

```powershell
$env:RUN_LIVE_OLLAMA = "1"
python -m pytest tests/live_provider_test_ollama.py -q
```

The browser action `Run demo assessment` was clicked against the local preview and returned a completed demo run with a generated ID. The run was persisted below the configured local data root in `demo-runs/<run_id>.json`; no Nmap or provider call was made.

An early browser check correctly reported that Nmap was unavailable before the local Nmap installation was repaired. The current runtime now resolves `C:\Program Files (x86)\Nmap\nmap.exe`, reports Nmap 7.991 through the authenticated status endpoint, and exposes the active Nmap interface choices. Live scanning must still be limited to a network the user owns or is authorised to assess.

The dashboard was then reduced to a scan-first landing page. Browser verification confirmed the logo, centred `Scan` button, private-network notice, and scanner status. With Nmap available, progress is calculated from persisted discovery/service coverage rather than an invented timer, and the result page reads devices, services, and findings from the saved JSON document.

Live scan evidence: the repaired Nmap 7.991/Npcap 1.88 stack completed scan `f67a2d87-79ea-4b6b-8e91-b1c0b6f22353` against the explicitly configured `192.168.56.0/30` scope. Discovery completed with zero responding devices, so the result contains zero devices and zero findings. This is not evidence that the network is secure; use the known-host mode or a correctly configured authorised lab subnet when devices do not answer discovery probes.

The active Wi-Fi scope was then identified as `192.168.0.0/24` and scanned with the same bounded profile. Scan `374670da-9017-439e-98ec-ac51dc6ae87c` completed with 10 observed devices, 7 open selected TCP services, and 4 deterministic review findings. After discovery, UI progress uses discovered-host count as the denominator so the percentage reflects actual service-scan work rather than all 254 possible addresses.

The latest scan `d34cff71-a15b-47a2-b850-c3cde0eda545` completed with 11 devices, 7 open selected TCP services, and 4 findings. Local hostname resolution identified `Namaiki.cable.virginm.net` for `192.168.0.216`; other hosts had no resolvable name and remain labelled `Unknown device`. The results UI now uses device name/IP and service port instead of internal rule/service identifiers.
## Follow-up verification: 24 September 2026

- `python -m pytest -m "not live_lab and not live_provider and not browser" --basetemp .pytest-brief-review-fix04`:
  150 passed, 2 deselected. Includes exclusive app ownership, lock release after a
  startup failure, short temporary names, invalid-update preservation and atomic
  backup/replacement failure tests. The long-path guidance archive case passes.
- `node tests/dashboard_ui.test.mjs`, `node tests/report_ui.test.mjs`, and
  `node tests/live_server_bridge.test.mjs`: 16 passed. Covers status/session/storage
  distinctions, refresh during analysis, backend recovery without browser storage,
  completed-report reopening, retry after connection loss, and report overview actions.
- `RUN_BROWSER_TESTS=1 RUN_LIVE_OLLAMA=1 python -m pytest tests/browser_test_workflow.py tests/live_provider_test_ollama.py --basetemp .pytest-fix03`:
  2 passed. Edge uses synthetic network/AI for browser flow; the separate provider
  test calls the real local llama3.2:3b model with synthetic facts. Its saved report
  was `analysis_status=ready`, prompt 4.1.0. The synthetic browser screenshot was
  visually inspected for readable layout and visible limitations.
- `python -m app doctor` verified Nmap 7.991 in `.venv` and `.venv-brief`.
  No authorised-network Nmap run was performed. Pi-hole was not connected.
- Python F-series lint and JavaScript syntax checks passed. Existing deprecation
  warnings remain; they are separate from functional test failures.
