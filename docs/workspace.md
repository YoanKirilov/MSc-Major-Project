# Workspace organisation

Keep application code in `app/`, tests in `tests/`, operational helpers in `scripts/`,
and explanation/decisions/evaluation records in `docs/`.

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
study tests. Lint, formatting, Python tests, all three JavaScript suites and JS syntax
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
