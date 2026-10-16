# WebKit layout follow-up — 16 October 2026

## Scope and confirmed causes

No device scans, live model generation, Pi-hole/NVD requests, normal report changes,
Git pushes or Windows security-policy changes are part of this work. Existing audit
changes in the worktree are preserved.

There are two separate problems:

1. GitHub's Ubuntu WebKit tests previously launched, then failed four narrow-screen/
   enlarged-text reflow cases, especially Settings. These remain release blockers
   until the changed source passes a functioning WebKit build.
2. This Windows installation blocks the test browser before it loads the app.
   Read-only Code Integrity events **3033 and 3077** name Playwright's bundled
   `webkit-2359/icuin77.dll`; the DLL does not meet the enforced signing policy.
   Its Authenticode status is `NotSigned`, and Smart App Control's
   `VerifiedAndReputablePolicyState` is `1`. This explains the recorded browser exit
   `3236495362` (`0xC0E90002`); it is not an application JavaScript exception.

Microsoft documents that unknown unsigned code can be blocked by
[Smart App Control](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/overview).
No protection was disabled, no file was unblocked/replaced, and no exception was
added. Reinstalling an identical unsigned DLL is not a demonstrated remedy.
WSL has no installed Linux environment here, and Docker is not installed.

## Changes implemented

- Settings retains native `fieldset`/`legend` semantics, labels, control IDs,
  disclosure and save behaviour. Its layout grid is now an ordinary inner
  `.form-section-body`, avoiding reliance on the special native fieldset grid
  renderer and intrinsic sizing.
- Explicit `minmax(0, 1fr)` tracks allow Settings and shared field controls to
  shrink to their available width. Legends are constrained to the container and
  may wrap. The single-column form rule is scoped to Settings; Saved reports keeps
  its two-column desktop filters and single-column mobile layout.
- No page-wide clipping, hidden overflow, reduced text size, browser skips or
  relaxed overflow thresholds are used. CSS cache versions are updated in all
  three page shells.
- The original failing appearance/responsive/forced-colour assertions now report
  oversized element IDs/classes, rectangles, minimum widths and grid tracks.
  They do not log device names, settings values or session credentials. The
  responsive check retains zero-pixel tolerance; existing one-pixel appearance
  tolerance is unchanged and has a unit regression.
- A focused Settings regression expands advanced settings and exercises a long
  synthetic adapter identifier, control/legend containment and 44px targets at
  320/390/768/1440 CSS pixels with 100%/125%/200% text. It edits only its isolated
  browser DOM, never saved settings.

These are compatibility corrections, **not a verified WebKit resolution yet**.
The exact original WebKit overflow has not been reproduced on this protected
Windows machine. The new stress case already passed Chromium/Firefox before the
CSS change, so those baseline passes do not establish WebKit behaviour either.

## Verification record

- Initial test setup lacked its parent artifact directory; no browser cases ran.
  The first stress fixture then tried filling a deliberately disabled network
  input. Both cases failed at that fixture action, not a layout assertion.
- Corrected baseline `.test-artifacts/webkit-reflow-20261016-baseline/`: two
  Chromium/Firefox stress cases passed against the original layout.
- Offline gate `.test-artifacts/checks-fa13837f29/`: **864 Python passed**, five
  Windows environment skips, **252 JavaScript passed**, 27 syntax checks; Ruff and
  all 181 Python files' formatting passed. The four additional Python cases guard
  the unchanged overflow tolerances.
- Installed-package gate `.test-artifacts/package-850b3e4631/` passed dependencies,
  seven pages, 29 assets and synthetic report create/reopen/delete/Undo. Its
  source/build/installed/current hash checks passed; no normal reports were used.
- Broader appearance/responsive/UX/Settings matrix
  `.test-artifacts/webkit-reflow-20261016-final/`: **34 Chromium/Firefox cases
  passed**, no skips, in 340 seconds. During this run the form-column rule was
  narrowed to Settings so it would not override the desktop history layout.
- Final targeted confirmation after that scoping change and added history
  geometry assertions, `.test-artifacts/webkit-reflow-20261016-confirm/`:
  **10 passed**, no skips, in 122 seconds. This reruns all four originally failing
  test types plus the new Settings stress case in both available engines. It also
  verifies that desktop history filters remain two columns and narrow filters
  remain one column, with dark/light enlarged text. This is a targeted final-source
  confirmation, not a new all-engine CI run.
- Inspected screenshots include narrow Settings display preferences and expanded
  Settings at 200% text. This is visual review of emulation, not physical-device
  evaluation. Final Ruff/181-file formatting and `git diff --check` passed.

## Required next verification

The first pushed commit is `3ca2b74`. Its
[GitHub run](https://github.com/YoanKirilov/MSc-Major-Project/actions/runs/38911284256)
passed security and all dependency checks, but all four combined-engine test jobs
were cancelled at their 25-minute cap. Linux progress included failed assertions;
the cancellation occurred before pytest's end-of-run tracebacks, so this is not a
passing WebKit result or evidence of a timeout-only problem.

The workflow now separates the three engines into independent matrix jobs, keeping
**every** Linux/Windows, Python 3.12/3.14 and Chromium/Firefox/WebKit combination.
The 25-minute job bound and individual test/overflow limits are unchanged. All
browser prerequisites remain installed because a few older workflow tests explicitly
use Chromium. `PYTEST_ADDOPTS=-x -vv` and unbuffered output give the first failing
case/traceback promptly; failures block that job, never become skips or success.
The other matrix jobs continue independently. A complete successful run must still
execute all selected cases. Follow-up verification is pending; no green claim is
inferred from reorganising the jobs.

For a functioning Linux/macOS test environment, install the pinned development
dependencies and browsers, then run:

```sh
python -m playwright install --with-deps chromium firefox webkit
python scripts/check.py --browser --browser-engines chromium,firefox,webkit
python scripts/check_package.py
```

Do not clear the WebKit issue based on Chromium/Firefox or on a Windows launch
failure. If it still overflows, use the newly emitted element geometry to isolate
the remaining cause. A vendor-signed/trusted compatible Windows WebKit build or a
separate supported test environment is needed to test it locally without weakening
this PC's protection. Physical Safari/iPhone and assistive-technology checks remain
separate, unperformed evaluations; Playwright WebKit is not branded Safari.
