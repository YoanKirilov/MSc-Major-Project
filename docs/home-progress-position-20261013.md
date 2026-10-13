# Stable home-page scan progress — 13 October 2026

## Request and confirmed cause

Starting or reconnecting to a scan moved its progress card above the home-page
setup. `dashboard.js` explicitly inserted the card before `.scan-landing` and
scrolled it into view. Running-state CSS also changed the setup's top spacing.
This was a presentation decision, not a lost scan or a second scan submission.

## Implemented fix

1. Retain the template's order: scan setup, progress, then errors. Neither normal
   recovery nor error recovery relocates the progress element.
2. Remove automatic scrolling on start/reconnect. Progress stays below setup;
   users can scroll to it without the app moving their reading position. Keep the
   disabled "Scan in progress" action and existing polite stage announcements.
3. Anchor the home grid consistently from the top in both idle/running states.
   Do not apply running-state top padding. This also avoids setup re-centering
   when the additional card appears on a tall screen.
4. Update the dashboard script version and regression contracts. Preserve fixed
   targets, pinned-job recovery, cancellation, parallel jobs, analysis waits,
   saved results and all scan/network safety boundaries.

The progress card can be below the visible screen on a phone. That is intentional
for the requested stable order; this change does not auto-collapse setup or move
focus. No Nmap, AI, naming, CVE or JSON-storage behavior changes are included.

## Design review and proposed next work

These are recommendations, not additional implemented features or a claim of
WCAG conformance. Keep the requested empty-start, one-report-per-scroll history
behavior and test proposals with readers who have no computing background.

Two remaining presentation issues were confirmed in the synthetic running-page
screenshots; neither is fixed by the position change:

- The setup still says "Ready to scan" above "Scan in progress". Replace readiness
  copy during a running/reconnecting job with one consistent status and a brief
  "Progress is below" cue. Restore accurate readiness/error copy when that job is
  no longer active. Preserve pinned IDs and do not submit anything to refresh copy.
  [W3C status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).
- Desktop Cancel scan and Set up another scan actions are adjacent with too little
  separation. Give them a wrapping action row with an explicit spacing-token gap,
  retaining the existing targets, native controls and mobile reachability.
  [GOV.UK button grouping guidance](https://design-system.service.gov.uk/components/button/).

Address those two feedback/spacing issues first in a follow-up, then the following
design priorities. They are presentation issues, not scan completion failures.

1. **Make display preferences easy to find on every page.** Theme/larger-text/
   movement controls currently live at the bottom of each report although they
   affect all pages. Add a consistently placed Display preferences entry in
   Settings or the shared header. Essential reading controls should not require
   reading a whole report first; details are better reserved for secondary content.
   [GOV.UK details guidance](https://design-system.service.gov.uk/components/details/).
   Verify native keyboard access, retained values, narrow layouts and blocked storage.

2. **Shorten the Deep device selector.** `setup-tools.mjs` places name, address,
   saved check status and date together in every option. Prefer name + address,
   then put the selected device's status/date in a short description below. Retain
   manual addressing and native selection; test whether a smaller set of choices
   is clearer before introducing a custom searchable combobox.
   [GOV.UK select guidance](https://design-system.service.gov.uk/components/select/).
   Verify unknown/conflicting names, long names, keyboard selection and unchanged targets.

3. **Offer Show next report after the revealed reports.** The existing control is
   above the list, while explicit loading correctly moves focus to the new report.
   A companion at the end would reduce keyboard backtracking. Preserve zero initial
   reports, one-entry requests, automatic-scroll focus stability and retained entries.
   This applies the principle of an understandable navigation sequence, not a
   finding that the existing page necessarily fails an accessibility criterion.
   [W3C focus-order guidance](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html).
   Verify repeated Tab/Enter loading, filters, no-more results and append errors.

4. **Add task-progress semantics to the visual bar.** The existing graphic is
   a `div`/`span`; use native `progress` or a labelled `progressbar`, indeterminate
   during the Deep device check. Preserve the existing throttled status and stage
   announcements. Phase-weighted percentages are not estimates of time remaining;
   explain that distinction without making up a completion time.
   [W3C progressbar versus meter guidance](https://www.w3.org/WAI/ARIA/apg/patterns/meter/),
   [W3C status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).
   Verify accessible values, indeterminate stages, queued/failed/cancelled cases and
   screen-reader behavior; do not announce every polling tick.

5. **Simplify the report action hierarchy.** Run again, reload, retry devices,
   naming and explanation retry can share the report header. Keep recovery actions
   visible when needed, group optional maintenance, and make the first useful
   review action more prominent. One clear primary action is easier to identify.
   [GOV.UK button guidance](https://design-system.service.gov.uk/components/button/).
   Verify that incomplete evidence stays visible and readers can identify what to do
   first without interpreting technical severity codes. Validate with participants
   before undertaking another broad visual redesign.

## Verification

The new synthetic browser regression reproduced the original defect before the
fix: the Light progress card preceded setup. Artifact:
`.test-artifacts/progress-workflow-before-20261013-e136d7/`.

The final isolated offline gate passed **602 Python and 138 JavaScript tests**,
lint, formatting for 148 files and seventeen module syntax checks. Artifact:
`.test-artifacts/checks-6b816ef71b/`. Dashboard cases cover normal Light/Deep starts,
refresh, metadata outage, missing reports, pinned targets and no extra submissions.

The offline installed-package check passed **six pages, eighteen assets and demo
read/create/reopen**, with both dependency checks clean. All **93 app files**
match the installed package byte-for-byte, including changed dashboard assets.
Artifact: `.test-artifacts/package-c2d4163169/`.

The focused synthetic browser workflow passed **19 cases** in Chromium, Firefox
and WebKit: root/profile-specific pages; mobile, desktop and tall desktop;
unchanged setup position/scroll on start; progress below setup after refresh;
no duplicate submissions; independent Light/Deep jobs and cancellation; analysis
wait/outage/retry; history reopening and Run again. Artifact:
`.test-artifacts/progress-workflow-20261013-c7d850/`.

The responsive/home/appearance selection passed **12 cases** across the same three
engines, covering eight viewport sizes from 320 to 2560 pixels, native keyboard
mode selection, 200% home text, Dark/Light and larger-text reflow on all page types.
Artifact: `.test-artifacts/home-progress-reflow-20261013/`.

Two final-source Chromium workflow cases were repeated to capture mobile/desktop
Light/Deep progress screenshots. All four were visually inspected: progress is
below setup, addresses and controls stay within their cards, and the remaining
readiness-copy/action-spacing issues above are visible. Artifact:
`.test-artifacts/progress-workflow-screens-20261013-e7492c/`.
The screenshot-only test additions passed focused Ruff checks and formatting.

All selected final checks passed; this is the complete offline gate plus scoped
browser/package verification, not a rerun of every historic browser scenario.
No real network scan/provider call or normal app/data mutation occurred. Real
devices, participant understanding and assistive-technology testing remain
separate from synthetic automation.
