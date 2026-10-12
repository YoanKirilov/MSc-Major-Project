# Workspace organisation

Keep application code in `app/`, tests in `tests/`, operational helpers in `scripts/`,
and explanation/decisions/evaluation records in `docs/`.

## Presentation organisation — 9 October 2026

See [the UI/UX execution record](ui-ux-implementation-20261009.md) for the 28-item
brief and verification. Shared header/footer includes prevent separate page shells.
Report state and writes remain in `scan.js`; `devices.mjs`, `finding-list.mjs` and
`editor.mjs` handle cohesive display/interaction responsibilities. Notes/nickname
revision ownership and saved evidence are unchanged. CSS is organised into component
and responsive sections rather than duplicated small-screen overrides.

The [eight follow-ups](ui-ux-followups-20261009.md) add `report-view.mjs` for validated
per-tab reading-state/disclosure restoration and navigation offsets; controller
state/writes still belong to `scan.js`. `presentation.mjs` owns the common review
title. Announcement placement shares `devices.mjs::deviceResultEntries` rather than
duplicating the address selection rule.

The application ships seven templates (including the base and two shared includes),
15 JavaScript modules and one stylesheet. The reachability regression checks every
routed template and static import. The default gate now runs eight JavaScript suites
and 15 module syntax checks. No user data, prior environments or evidence directories
were deleted for presentation cleanup. The dated counts below describe older versions.

## Review — 8 October 2026

The later [home live review](home-live-review-20261008.md) implements the connection
query, summary/search/picker date and pinned-build follow-ups. Actual home scans and
installed-package/browser/security verification are recorded there; normal reports
were preserved. No unused source file was proven safe to delete.

The [offline code review](offline-code-review-20261008.md) records the latest source
organisation and verification. All 67 application Python modules, five templates
and 12 assets remain reachable; no unused source file was proven safe to remove.
Older dated counts and cleanup records below describe their earlier version.

- `scanner/cpe.py`: pure fingerprint parsing/eligibility, independent of NVD HTTP.
- `scanner/cve.py`: bounded public-reference HTTP orchestration and compatibility
  aliases; `scanner/cpe_identity.py`: conservative dictionary resolution.
- `schemas/common.py::observation_time`: shared aware-UTC parsing for comparison,
  historical naming and cross-report nickname reuse; saved timestamps stay intact.
- `static/js/notes.mjs` and `nicknames.mjs`: independent revision-protected display
  snapshots, not evidence storage or scanner state.
- `tests/fixtures/offline.py`: accidental live-work guards for synthetic tests.

The default gate runs six JS suites and 11 module syntax checks. It excludes
browser, live-provider, lab and reader-study work. `requirements-build.lock` now
provisions pinned tools for the owned build environment in `scripts/check_package.py`;
an optional prepared wheelhouse supports offline build/install checks. The later home
session verified this workflow. Existing environments/artifacts were not deleted.

## Cleanup review — 2 October 2026

The follow-up live-test cleanup removed only regenerated `build` and `.ruff_cache`
after archiving their 88 files in
`.test-artifacts/cleanup-667f335d092e4a98b25dd46a7cf7a152.zip`.
The new CVE module raises the active JavaScript count below from eight to nine.
A regression now walks routed templates and local static imports to detect orphan
assets and missing dependencies. No additional source file was found unused.
See [the live verification](live-check-20261002.md) for results and remaining limits.

All application Python modules remain reachable from the CLI/app entry point.
All five templates and all eight JavaScript modules have active page/import users;
there is no unused HTML or JavaScript file to delete. Framework routes, validators
and mDNS callbacks were checked separately because registration invokes them without
a normal direct function call. Demo APIs/fixtures and the deferred Pi-hole connector
remain supported code, not abandoned files.

Removed the unused `parse_discovery` wrapper; the supervisor already calls
`parse_discovery_details` to retain discovery identities. Removed obsolete score-ring,
score-inner and danger-icon CSS, including their mobile rules. Replaced the report's
pass-through service-label wrapper with an alias to the existing shared import.
The remaining application boundaries and visible layout are unchanged.

Archived and removed three generated/empty root folders: `build`, `.ruff_cache`
and `front end`. Their 91 files are recoverable from
`.test-artifacts/cleanup-d550a8734dac4b36aac228a8407d5ea6.zip`; the empty directory
needs no content recovery. This supersedes the earlier locked-folder note below.
Preserved saved scans, `.preview-data`, test evidence, virtual environments, package
metadata, IDE settings and historical documentation. See [testing](testing.md) for
the post-cleanup regression results.

## Source map

The device-detail implementation is organised into focused parts:

- `app/jobs/enrichment.py`: optional-check scheduling, cancellation and checkpoints.
- `app/scanner/details.py`: bounded HTTP, UPnP and selective NetBIOS requests.
- `app/scanner/observations.py`: pure interpretation and safe, bounded detail formatting.
- `app/profiling/history.py`: conservative comparisons of saved evidence.

AI wording validation is separate from orchestration: `app/explanations/validation.py`
contains the pure acceptance rules; `service.py` owns provider calls, batching and saves.
The 27 September extraction preserves the validator body and prior service entry point.
`tests/unit/test_layout.py` now checks module reachability and this delegation. Nothing
was deleted during this review; generated verification outputs remain in ignored folders.

The follow-up import audit reached all non-initialiser application modules from the
entry points, and the page/asset regression covers every shipped static asset. This is
evidence of use, not proof that every branch is needed. No source file was deleted merely
to make the tree smaller; saved reports and historical documentation remain intact.

## Repeatable verification

After installing the development dependencies in your chosen virtual environment:

```powershell
python scripts/check.py
# Optional: synthetic browser scans and the real loopback-only Ollama service
python scripts/check.py --browser --ollama
```

The default command never opts into browser/provider/lab tests, even if old opt-in
environment variables remain in the shell. Both variants exclude live-network and human
study tests. Lint, formatting, Python tests, all four JavaScript suites and JS syntax
checks stop at the first failure. All new run artifacts live under `.test-artifacts/`.
VS Code also provides **NetGuard: Check offline**.

## What was cleaned up

Fifty old generated test/build/cache folders were removed after their contents were
archived in `.test-artifacts/cleanup-527a015dccf1424ab01f6a51f256ffd9.zip` (3,674 files).
The archive contains relative original paths; extract selected files into a separate
directory when needed. Old verification paths in dated notes refer to that archive.
The temporary build regenerated for the final package check was also removed, with a
separate backup at `.test-artifacts/cleanup-3428999c368b4a8498a94e3b1c70dc10.zip`.

Seven other historical test/review folders and the old coverage file were moved intact
to `.test-artifacts/historical/`. They were not treated as expendable user scan data.
`BUILD_STATE.json` moved to `docs/archive/build-state-20260921.json`, explicitly marked
historical. `3.png` moved to `docs/reference/scan-ui-20260921.png`; it is a historical
screenshot containing network identifiers, not an application asset. Review/redact it
before sharing outside the project.

The empty `front end` folder could not be removed because another process holds it open.
It has no runtime role. Close the terminal/editor/process using it before removing it;
no unknown process was stopped for cleanup.

Preserved: `.preview-data`, the configured application data folder, original source backup,
all virtual environments, IDE preferences, installed package metadata and staged Git work.
`.venv` runs the app; `.venv-brief` and `.venv-package` are development/package verification
environments used here. They are not duplicate source folders and are not automatically deleted.

## Future cleanup

Stop build/test commands first, then preview the narrowly scoped cleanup:

```powershell
.\scripts\clean_workspace.ps1
# Inspect the exact target list before applying:
.\scripts\clean_workspace.ps1 -Apply
```

Only named generated root folders are selected. The script refuses linked paths and
configured application data, creates and checks a ZIP before deletion, uses native
literal-path operations, and leaves locked folders alone. It does not prune the artifact
archive, saved reports, virtual environments or source files.

## Verification-server handoff

After agent-run live verification, stop the agent-owned backend once all jobs have
finished. Do not leave a hidden server on port 8765 and then ask the user to start
the VS Code task: the port and JSON instance lock correctly prevent a second
backend. Verify the process identity and idle status before stopping it. Never
stop an unrelated listener or interrupt a scan merely to free the port.
The Start backend task reveals its terminal so startup failures and the local
session link are visible. Do not publish that session link in shared evidence.
