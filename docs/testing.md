# Testing status

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
