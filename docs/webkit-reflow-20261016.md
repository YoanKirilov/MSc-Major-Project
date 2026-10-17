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
- No page-wide overflow clipping, reduced text size, browser skips or
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

The split run at `385ec14`
([results](https://github.com/YoanKirilov/MSc-Major-Project/actions/runs/38914929505))
completed without the combined-job cancellation. All four Linux Chromium/Firefox
jobs and security passed. Both Linux WebKit jobs still failed the enlarged-text
Settings check: 348px scroll width in a 320px viewport, with no oversized visible
element border box. Windows jobs failed earlier, waiting for session bootstrap;
this is a separate startup failure, not proof of a WebKit launch/signing problem
on the hosted Windows runners.

Follow-up diagnostics therefore include internal scroll widths, text-node ranges
and temporary subtree probes on an already-failed synthetic page. Probes restore
CSS properties and never change the original failure decision. A browser regression
forces genuine overflow and checks both restoration and the unchanged failure.
Startup errors now include sanitised console errors and static/session response
status/MIME types rather than only an uninformative session timeout. Neither the
layout nor hosted Windows bootstrap is declared resolved at this stage.

## Confirmed remaining causes and targeted corrections

The diagnostic run at `696d512`
([logs](https://github.com/YoanKirilov/MSc-Major-Project/actions/runs/38941155578))
isolated the remaining issues:

- **WebKit dropdown internals:** enlarged text left `#scope-mode`'s visible box
  within its 250px field, but its field's scrollable width was 313px and the page's
  was 348px. Hiding only `#scope-mode` restored the page to 320px; hiding the header,
  display preferences, advanced section or Ollama button did not. This matches the
  [documented WebKit select/option overflow family](https://bugs.webkit.org/show_bug.cgi?id=284644).
  The correction limits overflow **on single-line native selects only**, not the
  page, form, labels or evidence. Native appearance, options and focus remain;
  multiple/list-box controls are excluded. Some engines compute this as `clip`
  rather than `hidden`; tests allow either, while retaining all page/containment
  assertions and checking that native appearance has not been removed.
- **Hosted Windows module MIME types:** static `.mjs` responses were HTTP 200 with
  `text/plain`, while `.js` responses were JavaScript. The startup module therefore
  could not import its dependencies and never created a session. Browsers require
  a [JavaScript MIME type for modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules);
  Python can inherit [Windows registry associations](https://docs.python.org/3/library/mimetypes.html).
  `AppStaticFiles` now supplies deterministic `.js`/`.mjs`/`.css` response types
  for this app only, without modifying the OS or global Python MIME map. It retains
  Starlette's path checks, validators, missing-file errors, HEAD and range handling.
  A locally simulated incorrect MIME mapping failed before this correction.

The earlier diagnostic calibration failures are not app regressions: a zero-height
empty box did not create a scrollable area, and browsers may serialise a previously
absent empty style attribute as an empty attribute. The final diagnostic regression
uses a non-empty oversized box and checks actual CSS properties/computed display,
including an existing `!important` value, plus the unchanged overflow failure.

Local confirmation of these targeted corrections:

- `.test-artifacts/checks-1aef13db38/`: **871 Python passed**, five Windows environment
  skips, **252 JavaScript passed**, 27 syntax checks, Ruff and 183-file formatting.
- `.test-artifacts/webkit-and-mime-20261016-final/`: **12 Chromium/Firefox cases
  passed**, no skips, in 115 seconds. Covers long native options/focus, style-probe
  restoration, narrow/enlarged themes, forced colours/text spacing and Settings
  error/save/disclosure interactions. The earlier control-only run passed eleven
  cases and rejected an overly specific computed-style expectation (`clip` versus
  `hidden`); no overflow assertion was relaxed to correct that expectation.
- `.test-artifacts/package-935c8574c7/`: dependencies, seven installed pages,
  29 assets, source/build/installed hashes and synthetic create/reopen/delete/Undo
  passed, including the new static-file responder.
- Seven MIME regressions simulate incorrect host mappings, check GET/HEAD,
  conditional/single/multipart-range responses, missing assets and traversal;
  the process/global mappings stay unchanged by the application.

Full per-engine GitHub confirmation is still pending, not inferred from these
local passes. Existing app
processes need restarting to load the new Python static-file responder. Windows
Smart App Control remains enabled; this does not unblock its unsigned local
WebKit DLL or claim physical Safari/assistive-technology testing.

## Follow-up after GitHub run 18 (17 October)

[Run 18 at `63cff66`](https://github.com/YoanKirilov/MSc-Major-Project/actions/runs/38942450107)
finished with security and five browser jobs passing. The deterministic MIME fix
allowed Windows browser startup; remaining failures were different:

- Linux WebKit still measured 348px at a 320px Settings viewport. Windows WebKit
  showed that the native theme overrides single-line `overflow` to `visible`.
  The next candidate uses `appearance: menulist-button` (not `none`) to retain a
  native select while allowing clipping of its closed control. Strict narrow/
  enlarged-text, fieldset bounds, option and focus checks remain. Failure-only
  diagnostics compare native sizing alternatives and restore original styles.
- Windows Python 3.12 Chromium found a real snapshot-sharing defect: two sequential
  calls could share one completed read when their clock ticks were equal. Snapshot
  sharing now uses a completed-read generation, not timestamps. Time still checks
  suspension/delayed monitoring. Frozen-clock regressions verify sequential reads
  refresh and a subsequent network change still stops the guard. Overlap tests
  explicitly synchronise thread arrival rather than assume a fixed sleep is enough.
- Windows Python 3.14 Firefox reached a report-state assertion before the initial
  report/session GETs had settled. Its navigation helper now waits for those reads
  (as other page helpers do), retaining the actual restored-state assertions.
- Windows Python 3.12 Firefox had 141 passing cases before the 25-minute whole-job
  cap; browser checks alone took 20m30s and installation another 3m48s. Windows
  jobs now have a 35-minute budget; Linux stays at 25 minutes. Installation includes
  Chromium (required by legacy end-to-end fixtures) and the selected engine only.
  All 12 OS/Python/engine combinations remain. Slow-test timings are now printed.

Local offline gate: `.test-artifacts/checks-5939ff77df/`, 873 Python passed, five
Windows privilege-related skips, JavaScript and syntax checks passed, Ruff passed.
Focused browser verification: `.test-artifacts/ci-fixes-20261017-b/`, 22 Chromium/
Firefox cases passed (no skips), covering narrow/enlarged Settings, native options,
diagnostic restoration, explicit/invalid device links and reload/back reading state.
`.test-artifacts/ci-network-20261017/` passed all 35 guard/listener cases after the
thread-arrival test was made deterministic. Installed-package verification in
`.test-artifacts/package-7636c4d5f9/` passed seven pages, 29 assets and synthetic
report create/reopen/delete/Undo. New GitHub results will be recorded after
completion; the native-select candidate is not yet declared a hosted WebKit pass.

Run 19 at `4f7c7ef` rejected the native-button appearance candidate on Linux.
Its failure-only probes measured 348px for native button appearance, zero-intrinsic
width, inline-size containment and column-flex parents. **Block flow for the field
parent restored exactly 320px**, preserving the native select. Paint containment
also restored 320px but would risk clipping focus indicators; removing appearance
worked but unnecessarily restyles a native control. The next correction therefore
uses ordinary block flow for form fields and explicit child spacing. Native select
appearance and overflow overrides are removed. The long-option regression now
checks the block wrapper instead of requiring a theme-dependent computed overflow
value. All page-width, fieldset bounds, enlarged-text, option and focus assertions
remain unchanged. Hosted verification remains required.

Final local verification of block fields: `.test-artifacts/ci-block-fields-20261017/`
passed 17 Chromium/Firefox cases (no skips), including all-page/deep-dialog reflow,
themes, enlarged text, long native options and forced-colour/text-spacing checks.
`.test-artifacts/checks-c1004ce1c0/` passed 873 Python tests (five Windows privilege
skips), 252 JavaScript tests, 27 syntax checks and Ruff/format gates. The GitHub
matrix must still confirm the real WebKit implementation and Windows timing.

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
