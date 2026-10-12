# Offline code organisation and review — 8 October 2026

Constraint: the user is at work. Do not run Nmap, local discovery, device probes,
live model/provider checks or a live application scan. Preserve existing source
changes, saved reports, settings, evidence and running processes.

## Execution plan

1. Review entry-point imports and routed template/asset dependencies. Delete only
   demonstrably unused source; do not mistake callbacks, demos or the deferred
   Pi-hole connector for dead code. Leave generated artifacts and environments alone.
2. Add test-only fail-closed guards against real scanner/shell launches and external
   socket/DNS traffic in non-live-lab tests. Keep synthetic Python process tests and
   in-process HTTP transports usable. Verify the guards before running the suite.
3. Add date-boundary regressions for previous-report selection, saved-name restoration
   and nickname reuse. Reproduce offset ordering and invalid-report interference;
   centralise timezone-aware UTC parsing without rewriting saved evidence.
4. Separate pure application-CPE/fingerprint validation from NVD HTTP orchestration.
   Remove the dictionary resolver's dependency back into its caller. Preserve old
   helper imports as compatibility aliases, response limits and conservative matching.
5. Run focused and full offline Python/JavaScript, lint/format, import/asset checks.
   Do not enable browser, live-provider, lab or reader-study tests in this work session.
6. Update the current source map and report exact outcomes and remaining improvements.
   Do not claim the live Windows adapter timeout is fixed or verified at work.

## Implemented changes and evidence

### Organisation: isolate pure fingerprint decisions

`app/scanner/cpe.py` now owns conservative application-CPE parsing and service
eligibility. `cpe_identity.py` imports this pure module directly instead of depending
back on its calling HTTP client. API eligibility/cache decisions use the same helper.
`cve.py` keeps compatibility aliases, protected by an identity/dependency regression.
No NVD endpoint, response limit, matching threshold or port-based guessing was added.
Non-string dictionary values are rejected rather than causing a parser exception.

### Confirmed date-edge defects fixed

Eleven new synthetic report cases reproduced seven failures before the fixes:

- One malformed previous report made the whole earlier-observation view unavailable,
  even when another recent, compatible report was valid.
- Earlier-view selection and service-history filtering/sorting could use date strings
  rather than actual instants. Offsets could select an older report, exclude a valid
  earlier observation or accept a report whose instant was in the future.
- Timezone-free current metadata could still produce a service comparison; direct
  nickname identity matching raised on invalid/mixed naive and aware timestamps.

`schemas/common.py::observation_time()` centralises timezone-aware UTC parsing.
Unknown/invalid/overflowing times return unavailable, not an invented local timezone.
Comparisons now order parsed instants; an invalid previous candidate is skipped
individually. Historical-name and cross-report nickname reuse use the same parsing.
The seven-day, same-scope, unique-adapter rules remain unchanged. Exact nicknames on
their own report still work without a usable timestamp. Original date strings, names
and saved report files are not rewritten. This protects legacy/imported data edges;
ordinary app-generated dates are already UTC.

### Safer offline verification

`tests/fixtures/offline.py` is an autouse test-only guard outside `live_lab` tests.
It blocks scanner/shell/adapter-tool subprocesses and non-loopback socket/DNS targets,
including multicast, reverse lookup, async connection and UDP endpoint paths.
Synthetic Python runner processes remain allowed; an explicitly selected browser
test may additionally use only its exact packaged Playwright driver. Browser opt-in
handling was tested without starting a browser. This is protection against accidental
test traffic, not an OS firewall or sandbox for arbitrary child code.

The first full guarded run blocked two older tests' real Nmap version checks:
doctor fields and session status. Those tests now inject a synthetic version; session
status also substitutes adapter choices and model readiness. These are test-isolation
fixes, not changes to real scanner detection. No Nmap process was allowed to launch.

## Verification completed

- Initial guard/process checks: **24 passed**; the runner uses only synthetic Python
  print/sleep/cancellation cases, not Nmap.
- Focused history, naming, CPE, dependency/layout and guard checks: **105 passed**.
- Final complete offline gate: **545 Python / 73 JavaScript tests passed**, with
  **9 opt-in tests deselected**. Ruff lint/format passed for 137 files and all 11 JS
  modules passed syntax checks. Artifacts: `.test-artifacts/checks-ea42cfcfa9/`.
- Static reachability covers **67 application Python modules**, **5 templates** and
  **12 assets**. No unused application file was proven redundant or deleted. The
  deferred Pi-hole connector, demo code and framework callbacks remain active or
  intentionally supported. Generated evidence/environments were left alone.
- `git diff --check` passed. Existing unrelated edits were preserved. Tests used
  isolated JSON folders, not normal reports/settings; no normal backend was started,
  stopped or restarted by this review. The visible layout did not change.

No live scan, local network discovery, real model generation, live CVE lookup,
dependency/advisory-service audit, browser session or reader study was executed.
Passing offline tests do not establish current home-network or real-provider health.

An additional offline wheel-build attempt was **not completed**. The initial sandbox
temp-file restriction was cleared for that diagnostic, but the existing quality
environment has neither `setuptools` nor `wheel`. No dependencies were downloaded or
installed to bypass this. Source imports/assets pass, but a newly installed wheel is
not claimed verified today. Yesterday's installed-package check is historical evidence,
not a pass for this extracted module.

## Improvements and remaining work, in order

1. **Windows adapter-query reliability:** retain the failed-closed network guard.
   Add query/queue latency instrumentation and controlled delayed/failing-query tests;
   compare a lighter structured connection source before changing it. Actual paired
   home scans must wait until the user is back on an authorised network. The prior
   timeout is not fixed or live-retested by this offline organisation work.
2. **Finish end-to-end saved-date consistency:** report comparison is now corrected,
   but `JsonStore._list_scans()` still sorts compact summary date strings and
   `storage/library.py` independently parses filter/device-picker dates. Normal UTC
   app reports are unaffected; legacy offset timestamps, timezone-free dates and
   future-dated picker records warrant focused tests and a shared policy. Preserve
   access to uncertain historical reports instead of silently deleting or rewriting
   them. Do not claim every date-related reader was repaired in this review.
3. **Reproducible/offline packaging:** prepare a dedicated pinned build-tool lock and
   reviewed local wheel cache, then verify a fresh installed wheel containing
   `scanner/cpe.py`. The build backend is currently isolated/resolved separately
   from the development lock; installing that lock does not provide a no-isolation
   offline build. Do not add build tooling to the running app environment.
4. **Continue small, tested boundary extractions:** `scan.js` and `jobs/supervisor.py`
   are each roughly 1,000 lines. Extract sections only when their dependencies and
   state ownership can be made explicit; preserve refresh, cancellation, focus,
   revision protection and evidence semantics. Avoid a cosmetic wholesale rewrite.
5. **Finish reader, physical-device/accessibility and Ubuntu evaluation:** follow
   the prepared consent/scoring protocol; synthetic/offline results are not participant
   data. Keep Pi-hole as deferred future work and the Windows shutdown reset separate.

Current architecture remains one loopback FastAPI backend with locked JSON storage,
bounded scan/AI jobs, deterministic findings and validated local wording. No database,
server/framework migration, scanner policy change or new online feature was introduced.
Restart the normal backend only when idle to load these backend module changes; do
not start a work-network scan to check them.
