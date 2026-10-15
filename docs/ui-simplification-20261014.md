# Requested interface simplification — 14 October 2026

User screenshots and explicit preferences supersede the earlier extra-control and
periodic-check recommendations. Preserve home layout, saved reports/recovery,
device inventory, scan facts and final explanations. Two requested specialist
agents review report flow and complete periodic/movement removal; root owns shared
visual styles and final integration. No source edits during the already-running
baseline live pair `.test-artifacts/live-review-20261014-g/`.

## Acceptance list

1. Saved reports: put the date guidance below the action row with clear breathing
   room; keep its search, 24-entry pages and safe Delete/Undo/Restore.
2. Main navigation: use the light-blue link colour in every state, retain a distinct
   hover/focus state, and move underline clear of descenders. Current-page state
   remains identifiable without colour alone.
3. Settings: remove the movement selector without adding a replacement setting.
   Honour operating-system reduced motion; retain theme and text size.
4. Remove periodic checks: no scheduler lifecycle, API, control, imports or shipped
   feature scripts. Preserve old monitor.json bytes/backup compatibility as archival
   data only; they must never schedule work. Preserve manual parallel-job admission,
   locks, Delete/Restore and AI-retry protection.
5. My devices: move the applied-view hint further below the buttons; retain its
   existing layout, labels, search, views and return context.
6. Results: move What changed after the results/tasks, before Supporting information.
   Remove the third device filter and its redundant reset shortcut. Ignore legacy
   saved values so a removed control cannot leave devices invisibly filtered.
7. Make both per-device action buttons equal, centred and comfortably spaced,
   including wrapped labels at larger text sizes.
8. Replace double-bordered report searches with one ordinary input and an adjacent
   Clear action. Preserve visible labels, keyboard focus and adequate target sizes.
9. Under task status remove Need help shortcut, Expand and Collapse buttons.
   Keep the single status selector and each task's own native disclosure.
10. Supporting information: stable topic buttons open one native labelled dialog;
    switch topic inside it, scroll only its content, Close/Escape return focus to
    the originating button without moving the page. Retain all technical evidence,
    comparisons, announcements, glossary, wording provenance and display choices.
    Existing glossary/section links must route correctly. Never reopen a modal
    just because old reading-state data recorded a disclosure.

## Reference basis

[W3C modal-dialog guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
informs labelled headings, keyboard containment, visible Close, Escape and return
focus. [MDN underline behaviour](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-decoration-skip-ink)
supports ink skipping/clear underline placement. [Device reduced-motion preferences](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion)
remain honoured independently of removing an optional app control. These references
guide implementation, not a claim of accessibility certification.

## Verification

Record the baseline separately from the changed application. Run focused/full
offline suites and package installation; verify narrow/wide layouts, both themes,
larger text, keyboard/dialog focus and scroll stability, plus manual parallel-scan
admission and absence of scheduler endpoints. Use isolated JSON/artifacts only.
Do not delete existing reports or legacy user files. Record actual live/model
outcomes honestly, including unavailable simplification and unreachable devices.

## Implemented

All ten requested changes are implemented. Home and inventory layout remain;
changes there are limited to requested hint spacing, shared navigation and the
appearance-loader cache marker. Report search uses a single bordered input and
separate Clear action. Equal-size device actions occupy their own button grid,
outside the device disclosure. Removed controls have no dormant event handlers;
legacy device-filter values no longer hide results. The Supporting information
dialog preserves every evidence topic and its inner reading position, rather than
moving expanded topics through the page. Native Escape, Close and report-fragment
links preserve the appropriate focus/navigation behaviour. No modal auto-opens
from saved disclosure state.

Periodic runtime, routes, storage implementation, client modules and feature-only
tests were removed. Replacement tests ensure legacy settings remain inert and
unchanged, with private archival backup support. Normal parallel scan admission,
AI protection and Delete/Undo/Restore remain. See the
[removal record](periodic-removal-20261014.md).

## Verification results

- Final offline gate `.test-artifacts/checks-8ecdc94b51/`: 835 Python cases passed,
  five Windows link-privilege skips and 114 browser/provider/study deselections;
  all 229 JavaScript cases, 26 shipped script syntax checks, Ruff and 175-file
  formatting passed. Removed-feature tests were replaced with preservation and
  absence checks; lower suite counts do not mean the old scheduler remains.
- Screenshot-specific geometry, search shape, equal buttons, underline and help
  spacing: all 14 Chromium/Firefox cases passed in
  `.test-artifacts/ui-simplification-geometry-20261014-a/results.xml`.
  Phone/tablet/desktop widths, both themes and larger text were included.
- Appearance: seven Chromium plus seven Firefox cases passed. Motion is OS-only;
  saved theme/text choices, storage failure, narrow reflow, actual text/focus
  contrast and profile colours were checked. Artifact paths are in the removal
  record above.
- Native-dialog and simplified-device-control rerun: all eight Chromium/Firefox
  cases passed in `.test-artifacts/ux-dialog-scroll-d/results.xml`, including
  topic switching, Close/Escape/reopening, focus return, stable page position,
  narrow reflow and 200% text. Representative dialog PNGs were visually inspected.
- Initial package verification `.test-artifacts/package-0f3546e8a4/` correctly
  failed: old checkout `build/lib` copies reintroduced deleted scheduler files.
  `check_package.py` now builds an allowlisted fresh source snapshot, excluding
  caches, old build output and private data without deleting them. Four focused
  tooling cases passed, including the new stale-build regression.
- Corrected offline package `.test-artifacts/package-b60f9dc3d2/` passed seven
  installed pages, 28 static assets, removed-module/route/asset absence, synthetic
  report creation, reopening and Delete/Undo/Restore, plus clean build/runtime
  dependency checks. All 112 packaged app files matched both source snapshot and
  current checkout byte-for-byte.

- The earlier report-browser run had 19 passes and five failures. Four were exact
  task-label lookups fixed by explicit label association and covered by the clean
  eight-case run above. One library integration asserted an obsolete automatic
  Settings redirect; its corrected durable-save expectation passed the focused
  rerun `.test-artifacts/ux-report-library-e/results.xml`. All 24 originally
  selected report scenarios therefore have passing current-contract coverage;
  these overlapping reruns are not counted as 33 distinct scenarios.
- The wider responsive test also retained an obsolete expectation of zero saved
  reports before scrolling. The ordinary bounded page intentionally exposes both
  fixture reports immediately. The corrected full eight-viewport, six-route
  Chromium/Firefox matrix passed both cases in
  `.test-artifacts/ui-responsive-retest-20261014-b/results.xml`, including
  landscape, narrow reflow, 200% text and Chromium touch emulation.

- The wider `.test-artifacts/ui-simplification-regressions-20261014-a/results.xml`
  matrix finished with 92 passes and only the two obsolete responsive assertions
  described above failing. Their corrected rerun passed both engines. All 94
  unique scenarios in that batch now have passing coverage, including saved
  reports/24-entry paging/Delete/Undo/Restore, inventory/labels/return context,
  Settings, setup, keyboard/recovery controls and CVE presentation. Initial failed
  artifacts are retained, not relabelled as a clean single-run pass.
- Final Ruff, 175-file formatting and `git diff --check` passed after the test
  expectation fixes. Source app files remained byte-identical to the verified
  package; there were no subsequent application changes.

No scan traffic is allowed by these browser fixtures. The live pair
finished before these UI edits: see the separate
[baseline results](competitive-round3-20261014.md). Ollama was unreachable in
that pair, so actual model wording is not certified by this run; the factual
reports and explicit fallback remained accessible. Physical-device and novice
participant evaluation are not claimed.

Restart the normal backend after any active scans finish, then reload the page,
to unload its old scheduler/routes and load the current interface. The running
normal backend and existing saved reports were not modified or restarted here.
