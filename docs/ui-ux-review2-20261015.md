# UI/UX follow-up review — 15 October 2026

Scope: source-based review, focused implementation and isolated verification.
Preserve the current home, device hierarchy, Supporting information dialog,
pagination, recovery, scan facts and all existing worktree changes. No scans or
provider requests are part of this pass.

## Findings and chosen work

1. The report-title editor currently closes after a response without verifying a
   newer matching receipt, and does not announce success after close. Its failure
   message always says not saved, even if a response was lost after a real write.
   Verify the revision and server-normalised title, adopt valid receipts, announce
   one accurate final outcome and preserve the draft/reload recovery on uncertainty.
2. Settings and inventory warn about unsaved changes, but the report does not guard
   an edited title/nickname, pending save or failed checklist draft against leaving.
   Add a report-only, conditional native leave guard. Attach it only while dirty or
   pending; remove it when clean. Cancel/Escape remain explicit discard choices.
   Do not persist private drafts or perform automatic saves/retries.
3. The editor's local one-line check rejects only CR/LF/tab, while the server rejects
   non-printable label characters too. Add clear local validation for control/format/
   separator characters, preserving ordinary Unicode labels and the user's draft.
   Keep server validation authoritative; do not claim full Unicode equivalence.

## Research basis and limits

[WAI back/undo guidance](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o4p02-back-undo/)
supports protecting user work and predictable recovery. [MDN beforeunload guidance](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event)
explains native confirmation, user-activation requirements, mobile unreliability and
conditional listeners. The guard is best-effort protection, not durable draft storage
or a guarantee against browser crashes/mobile termination. No custom prompt wording
or automatic save is promised. [GOV.UK error guidance](https://design-system.service.gov.uk/components/error-message/)
supports useful local messages; retained local editor status and post-close global
success follow the prior single-outcome design rather than adding banners.

## Acceptance and verification

- Clean reports and unchanged/cancelled editors do not warn; typed drafts, pending
  saves and unresolved checklist drafts do. Successful saves remove the guard.
- A dismissed native leave prompt retains input and the current report; accepting
  intentionally leaves. Explicit Cancel discards without another prompt.
- Title success/removal is confirmed against a strictly newer matching receipt and
  announced once after native close. Failed/malformed/ambiguous receipts keep input
  and describe uncertainty rather than claiming success or definite failure.
- Invalid invisible characters produce a focused, useful local message and no write.
  Ordinary Unicode names still work; observations and severity are unchanged.
- Use new isolated JSON/artifact folders, focused JS/browser regressions, the full
  offline gate and installed-package verification. Check both browser engines,
  narrow/large-text layouts, keyboard and existing recovery paths. Preserve first
  failures and affected retests. Actual screen-reader/participant sessions remain
  separate evaluation work, not claimed by automated tests.

## Implementation

- `editor.mjs` exposes edit/pending state and a conditional native leave listener;
  the report combines that state with pending and unresolved checklist choices.
  Explicit Cancel and Escape notify the owner synchronously, before the browser's
  queued native close event. Busy editors cannot be dismissed halfway through a save.
- `notes.mjs` validates a title receipt against the strictly newer safe revision and
  normalised requested text. The report adopts that receipt before closing and uses
  its existing final-outcome region, not an additional banner. Ambiguous outcomes
  reload saved notes, keep the input and require an explicit further save.
- Invalid hidden characters receive a local explanation before a request. Ordinary
  Unicode labels remain accepted. This changes no saved observation or severity.
- Entry/module asset versions were refreshed. The existing layout, controls and
  Supporting information dialog were not redesigned in this pass.

## Verification record

- Final offline gate `.test-artifacts/checks-ba0fb7a4b7/` passed: **835 Python tests,
  five Windows link-privilege skips, 251 JavaScript tests, 27 shipped-script syntax
  checks**, Ruff and 178-file formatting. Browser/live/study cases are excluded from
  that gate and are reported separately below.
- Offline package `.test-artifacts/package-99b410587a/` passed seven pages, 29 static
  assets, dependency checks and synthetic report create/reopen/delete/Undo. All
  **114** packaged app files match both the fresh source snapshot and current app.
- The initial 18-case focused browser run in `ui-edit-recovery-20261015-a/` had four
  Chromium failures: Cancel could leave the warning active until the queued close
  event. The four-case diagnostic rerun passed before a source fix, confirming this
  was timing-dependent rather than proof of correctness. The implementation now
  clears explicit discard synchronously. New unit/browser regressions check discard
  and warning state within the same browser task, without a sleep masking the race.
- An early direct `node --test` invocation could not spawn a child inside the
  Windows sandbox; it executed no editor assertions. The final gate uses the normal
  supported direct-node runner. One test-line lint issue was corrected before the
  passing final gate.

- Final focused browsers in `ui-edit-recovery-20261015-final/` passed **22 cases**
  across Chromium and Firefox, including real native leave-prompt dismissal,
  successful title save/removal, pending saves, stale/mismatched receipts, explicit
  checklist retry, hidden characters and same-task Cancel/Escape race regressions.

- Wider browser matrix `ui-edit-regressions-20261015-a/` passed **47 of 50** cases.
  Its three failures were assertions for superseded behaviour: the library test
  expected a rejected checklist save to overwrite the user's draft with the saved
  value, and both nickname engines expected edit errors in the scan-coverage
  paragraph. Updated tests now require the retained draft plus explicit retry and
  local modal feedback plus unchanged coverage text. No production behaviour was
  relaxed to satisfy these old assertions. All **three affected cases passed** in
  `ui-edit-affected-20261015-b/`, including the remainder of the multi-tab scenario.
  Passing cases include report reading context, independent synthetic Light/Deep
  workflows, delete/restore, settings recovery, forced colours, increased text
  spacing, narrow layouts, keyboard navigation and both responsive engine cases.
  Overall, the 22 new focused cases and 50 wider cases have passing coverage across
  the final runs/retest, **not** one single clean 72-case invocation. Final Ruff,
  178-file formatting and `git diff --check` also passed after the test updates.

No network scans, real device probes, external lookups or normal report mutations
are part of this pass. Browser fixtures forbid scanner/provider calls and compare
synthetic report bytes after edits. Native leave prompts remain best effort;
mobile termination, actual assistive technology and participant comprehension are
not verified by these automated checks.

## Next useful evaluation

Use the existing [inclusive session kit](evaluation-session.md) with actual
nontechnical readers, keyboard/screen-reader users and a physical phone. Check
whether they can distinguish recorded observations, their own labels/review marks
and save uncertainty without coaching. Automated DOM/focus/reflow checks do not
establish comprehension or WCAG conformance. Preserve the current layout until
those sessions identify a concrete problem; do not add controls just to redesign it.
