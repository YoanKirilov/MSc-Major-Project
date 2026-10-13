# Saved-report reveal and accessibility — 13 October 2026

## Requested change and implementation plan

1. Replace the earlier eight-entry initial/history batches: opening Saved reports
   shows **zero** reports. Search/reset also clears the list and prepares filters
   without requesting reports. Only intentional downward scrolling begins reading,
   and subsequent gestures reveal one report each. A first keyboard control scrolls
   the page before revealing anything; a later Show next report control offers a
   one-entry alternative. Preserve request bounds, race rejection and readable errors.
2. Colour saved report titles by their recorded profile, not visited-link state:
   Light is blue and Deep is purple; hover/keyboard focus uses the opposite colour.
   Keep explicit type labels and neutral unknown-profile styling.
3. Remove justified alignment and its option. Keep natural left-aligned report prose
   and ignore legacy alignment state without losing saved searches/disclosures/scroll.
   Replace that option with Dark/Light appearance preferences.
4. Add larger-text and reduced-movement choices. Persist only these small allowlisted
   display values, separately from report state/evidence. Respect device-level reduced
   motion regardless of the selected preference; handle blocked browser storage.
5. Validate zero-start/one-entry gestures, keyboard alternatives, filters/errors,
   both palettes, enlarged/narrow layouts, contrast, refresh and packaging using
   synthetic reports. Do not scan any real device or call AI/CVE/Pi-hole providers.

## Accessibility design references

Report type remains written in text because colour alone must not identify it.
[W3C use-of-colour guidance](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).
Blue/purple shades adapt to the selected palette so text remains readable, including
on hover; sampled text and focus colours are checked rather than assuming a colour
name guarantees contrast. [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
Larger text remains compatible with browser enlargement and reflow.
[W3C resizing guidance](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html).
Reduced movement turns off decorative animation, transitions, smooth scrolling and
hover translation. [W3C interaction-animation guidance](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html).

## Architecture and limits

`history-feed.mjs` retains submitted filters and one-entry offsets; `history.js`
consumes a wheel burst, touch swipe or non-repeating scroll key once. Initial layout,
focus, zoom and programmatic scrolling alone must not reveal entries. The empty
history stage reserves scroll space even on a large display. Loaded reports remain
readable; nothing is deleted when scrolling away. JSON whole-library matching before
pagination remains unchanged, so this is not a database/index performance change.

`appearance.js` is a same-origin classic head script, run before the stylesheet on
all page shells. It restores small versioned display choices without inline-script
CSP changes, applies root datasets and binds native controls on DOM readiness.
Blocked/corrupt storage cannot block reports; no credentials, identifiers or scan
facts are saved in the appearance key. Cross-tab display changes synchronize without
write loops. Per-report reading filters/disclosures stay in their separate tab state.

These are targeted accessibility improvements, not a WCAG certification or proof
that every nontechnical reader understands the report. Physical devices, assistive
technology and participant evaluation remain necessary. Potential later additions
are a first-run guided tour and user-tested high-contrast presets; avoid adding new
controls without confirming a real need.

## Verification

Initial focused checks passed 14 history-state JavaScript cases, 27 zero-start/
gesture browser cases and 15 appearance browser cases across Chromium, Firefox
and WebKit. Nine appearance-module and eleven reading-state JavaScript cases also
passed, along with the existing 26 report-rendering cases. Sampled report text in
both palettes met 4.5:1 contrast and sampled keyboard outlines met 3:1; these samples
do not constitute a whole-site conformance audit.

The broader `.test-artifacts/checks-9a7e5dbe7a/` run ended with 773 passes, six failed
old history contracts and one WebKit launch-timeout setup error; one real-provider
test was deselected. The failures expected immediate empty-library lookup or a
nonzero-height initial report list. Those tests now check the heading/zero entries,
then explicitly scroll before expecting query outcomes. The setup error was a
180-second engine-launch timeout, not a report/page JavaScript exception; two
unchanged-source focused WebKit repeats passed, including traced navigations.
The broad run is retained as a failed run, not silently counted as green.

Final refinements shorten the motion label and keep empty/error feedback visible
after scrolling. The empty stage collapses only on error or ready/no-more state;
the initial/remaining scroll space stays available and focus is not stolen.

Finished-source results:

- **36 history browser cases** across all three engines passed, including actual
  in-viewport empty/no-match/error feedback after a large wheel gesture, unchanged
  query focus and one request/no displayed reports. Fourteen history JavaScript
  cases passed. `.test-artifacts/history-zero-feedback-final-20261013/`.
- **15 appearance browser cases** passed across all three engines, without setup/
  page errors or extra provider/mutation requests. The shortened Device settings
  label was visually checked at 320 px with larger text.
  `.test-artifacts/appearance-final-20261013/`.
- All **six corrected responsive/settings browser cases** passed, including the
  existing eight-size matrix and keyboard/form error tasks.
  `.test-artifacts/history-contracts-20261013-final/`.
- Final complete offline gate passed **602 Python and 136 JavaScript tests**, lint,
  formatting for 148 files and seventeen module syntax checks.
  `.test-artifacts/checks-2b436a0ad0/`.
- Offline installed wheel passed six pages, eighteen assets and demo create/read/
  reopen, with both dependency checks clean. All 93 application files matched
  source bytes exactly, including appearance/history modules.
  `.test-artifacts/package-51f94ef02d/`.

The full broad command was not rerun after these final small refinements and test
corrections; final affected-browser, package and complete-offline evidence is
separate from the earlier failed broad run. Existing saved data/backend were not
modified. Earlier eight-report evidence in the 12 October record is historical.
No real scans or providers ran. Physical devices/readers/assistive technology remain
unverified, not counted as passes.
