# Spacing and compact actions — completed 15 October 2026

Requested refinements began on 14 October; the separate inclusive research remains
in [UI/UX research and next steps](ui-ux-research-20261014.md). That document proposes
later improvements, not additional redesigns already implemented.

## Implemented

- Shared 8px spacing between fields/actions and their help text; matching 12px
  horizontal padding for form inputs, selects and action buttons. Search, Show
  and form action controls retain a comfortable minimum height of 48px.
- Removed the doubled form-action gap: the form already supplies its 24px gap,
  so the action row no longer adds another top margin. History and inventory help
  use the same action-hint component instead of separate ID spacing overrides.
- Device-footer actions remain equally sized and centred, but use narrower
  maximum width, reduced padding and tighter button-only line height. Standard
  fixture buttons are at most 60px tall instead of approximately 73px; targets
  remain at least 44px. Large text and long labels may wrap and increase height;
  no fixed maximum clips them. Body text and the home layout are unchanged.
- Retained the Supporting information dialog and all its content and behaviour.
- Updated the shared stylesheet marker consistently in all three page shells.

The 44px target is this product's comfort choice, not a claim that WCAG AA has a
universal 44px rule. [WCAG 2.2 target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
describes the 24px minimum and its exceptions.

## Verification

- `.test-artifacts/ui-spacing-20261014-b/results.xml`: all 18 Chromium/Firefox
  cases passed. Equal control/help gaps, matching padding, no doubled action gap,
  centred/equal compact buttons, 44px targets, single-border report searches,
  narrow/tablet/wide layouts, light/dark themes and larger text were checked.
  Standard phone/desktop button screenshots were saved and visually inspected.
- `.test-artifacts/ui-spacing-responsive-20261014-b/results.xml`: all four selected
  Chromium/Firefox cases passed: full eight-viewport/six-route responsive checks
  plus both-theme/larger-text reflow. Includes landscape and Chromium touch
  emulation; this is not physical-phone or actual assistive-technology testing.
- Final offline gate `.test-artifacts/checks-d7cd8220f3/`: 835 Python passed,
  five Windows link-privilege skips, 116 browser/provider/study deselections;
  all 229 JavaScript tests, 26 shipped syntax checks, Ruff and 175-file formatting
  passed. Isolated JSON folders were used throughout; no live scans were run.
- Offline installed package `.test-artifacts/package-f7df5e3e63/`: seven pages,
  28 static assets, removed scheduler absence, synthetic create/reopen/Delete/
  Undo/Restore and clean dependency checks passed. All 112 packaged application
  files matched both the snapshot and current checkout byte-for-byte; final
  `git diff --check` also passed.

Initial failures remain recorded rather than hidden:

- The first geometry run detected a real 6px horizontal offset: an empty later-
  lookup element consumed a flex gap. The footer now uses a one-column grid and
  hides empty children; the corrected complete geometry run passed.
- A Chromium keyboard case failed during early report interaction. Its test did
  not wait for reading-state restoration; it now waits for the application's
  existing explicit reading-ready signal and
  verifies focus before Enter. Both engines passed the full rerun; no arbitrary
  sleep was added and no keyboard failure is silently retried by the app.
- The first offline gate returned an unexpected 503 instead of the mocked capacity
  429 in one test. The isolated case and final complete rerun passed without a
  runtime change. Its cause was not established; the assertion now includes the
  response body so a recurrence has useful diagnostics. A subsequent gate stopped
  on formatting of the new readiness assertion; it was formatted before the final
  clean run. Do not describe either failed artifact as an initial clean pass.

## Remaining work

The research identifies a real source inconsistency between system-theme choices
in Settings and the report dialog, plus proposed content/navigation simplifications
and inclusive reader/assistive-technology evaluation. These are recommendations
for a later batch, not claims of implemented fixes or accessibility certification.
No normal report, private settings file or running backend process was changed by
the verification runs. Reload pages to use the revised styles.
