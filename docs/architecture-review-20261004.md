# Scan architecture review — 4 October 2026

## Scope and implementation

Reviewed request validation, Light/Deep command construction, supervisor admission,
queue/execution budgets, subprocess handling, network continuity, optional enrichment,
JSON checkpoints, AI validation/presentation and explicit CVE research boundaries.
Existing uncommitted work and normal saved reports were preserved.

The flow remains: validate an authorised target → persist the queued job → discover
and check services → save factual observations/rule findings → bounded optional
enrichment → local validated AI wording → final saved report. Light and Deep share
this pipeline but use different explicit port/script profiles. CVEs are requested
separately and saved as candidate references, not confirmed vulnerabilities.

Two changes were justified:

1. Moved pure coverage/failure/restart transformations out of the large supervisor
   into `app/jobs/transitions.py`. Existing supervisor entry points remain bound to
   those functions, preserving callers and lifecycle behaviour. A regression checks
   that transformations leave their input documents unchanged.
2. Added duplicate-ID admission protection. Previously an internal second `start`
   call for the same active ID could replace the tracked task/cancellation event.
   It now raises `SCAN_BUSY` before changing either. A regression preserves the
   original task/event and confirms only one active job. Normal API creation uses
   unique IDs, so this is a defensive lifecycle fix, not evidence that users were
   routinely creating duplicates.

No source file was identified as safely unused and removed. The module/template/
asset reachability regressions remain part of verification.

## Verification setup

The normal backend was left running. Live verification uses loopback port 8766 and
`.test-artifacts/architecture-live-20261004/data`, copying settings only—not private
session credentials or normal report history. Preflight checks the current network
against the authorised home scope; Deep requires fresh unique Sony identification.
These test reports will not appear in the normal app history. No real home-device
fingerprint is sent to external NVD. The test-owned server is stopped when idle.

## Verification results

- 396 Python tests and 50 JavaScript tests passed, including Chromium/Firefox/
  WebKit, lint/format for 119 Python files and nine module syntax checks.
  One real-provider test was deselected and the existing Starlette/httpx
  deprecation warning remains. Artifact: `.test-artifacts/checks-92840ac36e/`.
- Installed wheel passed six pages, ten assets, demo read/create/reopen and
  dependency consistency: `.test-artifacts/package-302ed75a2d/`.
- Light `1a7b654a-bfc1-411a-8189-7688a2a26286` completed in 240.9 seconds: all ten
  discovered devices checked, ten open services, seven review items, no scan
  warnings/errors. XML replay matched 150 service-state records/seven findings.
  Six AI records passed revalidation; two retained reviewed wording (`not_simpler`).
  Refresh/history and 320/390/768/1440-pixel layouts passed without page errors.
- The Sony did not advertise a name in this run, so automatic name-based Deep
  selection deferred. Its fresh Nmap MAC matched the preceding verified Sony MAC
  exactly. Deep was then resumed using this documented identity evidence, without
  repeating Light. No historical name was falsely marked as a fresh advertisement.
- A verification-script defect attempted to open a nonexistent Deep report after
  the intentional deferral. The script now skips unavailable profiles and records
  them as unchecked. This was a test-harness failure, not an app scan failure.
- During Deep `905fc1a2-e4b0-4bb3-b0d2-baf0d563ab39`, the user confirmed the Sony was
  in standby or switched off. After about ten minutes, the test was cancelled via
  the authenticated API rather than retrying long checks against a sleeping device.
  The app saved a cancelled report with one unfinished target, no completed device
  checks and AI not started. This is **not a passed full Deep assessment** and the
  empty result is not evidence that the TV is safe.
- Cancellation persisted correctly; Deep refresh/history, four viewport widths and
  both Run again choices passed without extra scan submissions or page errors.
  The test-owned server was stopped; the normal backend was not stopped or changed.
  Full live Deep verification of this revision still requires an awake Sony.

The running normal backend predates this code change. Restart its existing VS Code
task when idle to load the refactor; do not launch a second server against its data.

## Remaining improvements, not claims of completed validation

- The host-worker orchestration remains substantial; a later focused extraction
  could make retries and per-attempt checkpoints easier to review independently.
- Real-reader usability, physical-phone/assistive-technology and Ubuntu/raw-packet
  capability validation remain separate evaluation gates.
- Network continuity checks are best effort, not atomic network isolation.
- Live discovery counts vary with device availability; an unreachable device is
  retained as incomplete coverage, never silently labelled checked or safe.
