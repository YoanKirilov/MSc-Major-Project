# Inclusive UI implementation — 15 October 2026

Execute [IUX-01–07 research recommendations](ui-ux-research-20261014.md) without
changing scan scope, evidence, detection rules or authorisation. Preserve the home
layout, Supporting information dialog, 24-entry pages and reversible deletion.
Existing worktree changes and saved reports are not discarded.

## Work and acceptance

1. IUX-04: share display-control markup between Settings/report. Both expose
   dark/light/device theme and standard/larger text; OS reduced motion remains
   automatic. Feedback distinguishes applied from remembered, including blocked
   storage/cross-tab changes. No empty selected theme after choosing device theme.
2. IUX-01: revise visible wording to short literal sentences; retain unidentified
   devices, failed checks, zero-item limitations, local versus internet exposure,
   HTTP precautions, AI/fallback provenance and all factual priorities. Test the
   same facts before/after; no saved JSON rewrites.
3. IUX-02: foreground device name, household recognition, last recorded check and
   review/unfinished counts. Keep secondary history reachable through a disclosure,
   and keep drafts/search/favourites/paging/recovery behaviour. Never imply online
   status or verified identity from saved observations.
4. IUX-03: bounded explicit `?device=<saved ID>#devices-title` opens/highlights the
   intended device after reading state restores. Missing/invalid IDs produce a
   useful status without selecting another device or making a request. Retain
   browser Back, reading context and every original report record.
5. IUX-05: retain visible per-operation feedback but one deliberate live save
   announcement. Keep drafts and explicit conflict/uncertain-write recovery; no
   automatic repeated edits. DOM/browser checks do not establish spoken output.
6. IUX-06: extend keyboard/native-dialog, target/focus, 320px, enlarged-text,
   landscape, user text-spacing and semantic-label regressions. Record actual
   coverage, not screen-reader/physical-phone or WCAG certification claims.
7. IUX-07: extend the existing evaluation session kit with inclusive task protocols,
   familiar assistive technology, consent/ethics, anonymous scoring and unsafe
   interpretation measures. Recruitment and actual sessions require participants;
   prepare them but do not fabricate results.

## Ownership and order

Root owns shared templates/CSS, appearance implementation, integrated verification
and the existing evaluation-kit extension. The requested UX agent owns exact-device
report context and save announcements. Inventory agent owns device-card hierarchy
and target-aware report links. Plain-language agent owns editorial projections and
inventory/history prose. Coordinate strings/URL contracts across those boundaries.

Use isolated JSON/test folders and synthetic providers only. Run focused JS/Python/
Chromium/Firefox cases, full offline gate and clean installed-package verification.
No live network scans are authorised by this UI-only task. Preserve initial failed
checks and affected retests in the final evidence record.

## Implemented outcome

IUX-01–05 are implemented. IUX-06 has additional automated/browser coverage; actual
assistive-technology and physical-phone sessions remain unperformed. IUX-07 has a
prepared inclusive protocol and header-only task log, not fabricated participants
or results. These limits are part of the handoff rather than a claim of complete
WCAG conformance or universally understood wording.

The shared display partial fixes the Settings/report system-theme mismatch.
Preferences preserve immediate application, per-browser persistence, OS motion,
blocked-storage help and cross-tab updates. Persistent storage help is not a second
live announcement for the same edit.

Display projections now use shorter literal text for coverage, comparisons,
identity and AI fallback. Unit checks preserve priorities, exact counts/ports,
unfinished coverage, HTTP precautions and frozen input evidence. In particular,
not recorded accepting requests is not reduced to did not reply: a closed/filtered
response must not be misrepresented. No rules, providers or saved JSON changed.

Inventory cards show recognition, exact last-check date and review/unfinished counts
before secondary saved history. All recorded facts remain reachable. Exact device
links are encoded, bounded and matched without selector interpolation. They clear
an unrelated device search only when needed to reveal the target, expand only the
needed device page and preserve the reader's later view on reload/Back. Invalid,
missing or ambiguous IDs never select a substitute or start a scan.

Checklist outcomes use one designated final live region and visible static row
feedback. Unconfirmed saves keep the chosen status as a clearly labelled draft,
not a recorded completion; retry requires an explicit action. Nickname failures
remain inside the open native editor with the draft intact; success is announced
only after close/focus return. Inventory outcomes are focused non-live feedback,
avoiding the combined focus-plus-live path. DOM tests do not measure real speech.

The Supporting information layout is retained. A targeted Tab boundary handler
fixes the Chromium escape found by the new keyboard case while preserving the native
dialog, Escape, Close, per-topic reading position and focus return. Home, report
pagination and reversible deletion have not been redesigned.

## Verification evidence

- Full offline gate `.test-artifacts/checks-e070f3fb13/`: 835 Python passed, five
  Windows link-privilege skips and 120 browser/provider/study deselections; 246
  JavaScript passed, 27 shipped syntax checks, Ruff and 176-file formatting passed.
  The new report-context browser file was completed after that collection; the
  final all-file gate is recorded below.
- Final all-file gate `.test-artifacts/checks-66eef48557/`: 835 Python passed,
  five Windows link-privilege skips, 130 browser/provider/study deselections;
  all 246 JavaScript tests, 27 shipped syntax checks, Ruff and 177-file formatting
  passed. Final `git diff --check` passed; line-ending conversion warnings are not
  whitespace failures. No application files changed after the verified package.
- Reading/appearance/report-insights/responsive matrix:
  `.test-artifacts/inclusive-reading-20261015-a/results.xml`, 44 passed, no failures,
  errors or skips. Includes shared system-theme choices and OS/cross-tab changes,
  blocked storage, both themes/larger text, narrow/tablet/wide/landscape layouts,
  compact buttons, keyboard Deep setup and Chromium touch emulation.
- Focus/semantic matrix `.test-artifacts/inclusive-access-20261015-final/results.xml`:
  four passed, no failures/errors/skips. Includes native modal Tab/Shift+Tab under
  user text-spacing overrides at 320px, Escape, focus return, page position and
  visible-control labels/description relationships across the main pages.
- Inventory matrix `.test-artifacts/inventory-inclusive-browser-20261015-final.xml`:
  14 passed, no failures/errors/skips. Hierarchy/complete facts, encoded exact-device
  links, 24-entry paging, search/views, drafts/conflicts, focused outcome and Back/
  return context remain covered. Earlier pre-final copy run also passed 14 cases.
- Exact-context/save-feedback matrix:
  `.test-artifacts/inclusive-context-20261015-a/results.xml`, 20 passed, no failures,
  errors or skips. Explicit links, expansion to a late device, missing/invalid IDs,
  reload/Back, one designated save message, uncertain-write draft/retry and modal
  nickname success/failure were checked in both engines.
- Total browser coverage for this change: 82 passing cases across those four
  matrices. Synthetic fixtures reject scan/provider requests and verify original
  saved scan evidence bytes are unchanged. No live scans, Ollama requests,
  participant sessions or actual assistive-technology speech were run.
- Clean offline installed package `.test-artifacts/package-12a2045d7b/` passed seven
  pages, 29 static assets, synthetic report create/reopen/Delete/Undo/Restore,
  removed-scheduler absence and dependency checks. All 114 packaged app files
  matched both the snapshot and current checkout byte-for-byte.

Initial new accessibility checks are retained: three failures in the first matrix
and one isolated Chromium Tab failure. The visible-control checker originally
included descendants of collapsed disclosures; it now uses native visibility and
recognises label references. This was a test assumption, not unnamed active buttons.
The Chromium Tab escape was real and fixed in the controller. Corrected complete
four-case rerun passed. A Python raw-string warning in the new test was corrected;
it is not hidden by a warning filter. Initial test results are not relabelled as a
single clean run. Source/test lint and formatting passed after these fixes.

## Evaluation handoff

The existing [session kit](evaluation-session.md) now has inclusive synthetic tasks,
accommodations, ethics/consent, unsafe-interpretation checks and actual keyboard/
screen-reader/voice/magnification/physical-device follow-up. The new
[UI task log](evaluation-ui-tasks-template.csv) is header-only; original AI-comparison
scores remain separate. Recruitment, independent scoring and actual sessions need
participants and the university's approvals. No clearance or participant evidence
is asserted by this implementation. Browser emulation is not a physical-phone pass.

Reload pages for the updated styles/modules. Source, notes and test data remain
local; the running normal backend and existing private reports were not restarted,
deleted or altered by verification.
