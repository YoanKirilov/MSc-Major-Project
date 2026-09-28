# Testing status

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
