# Saved reports viewport fix — 14 October 2026

## Requested changes

The customer's follow-up replaces the previous one-row-per-gesture/empty-start
policy. The stored page already fetched 24 records, but the controller exposed
one per recognised gesture, so reaching the bottom could leave cached rows hidden.
This was a flawed interaction policy, not a scanner or saved-evidence error.

Use the [new research brief](ui-ux-recommendations-20261014-followup.md):

1. Render the whole selected page (at most 24) as an ordinary semantic list.
   No extra wheel/touch/keyboard gestures, virtualized rows or infinite page growth.
2. Use feature-detected IntersectionObserver only for short optional entrance
   animation. Rows stay visible/accessibly readable by default; focus removes
   animation immediately. Missing/failed observation cannot hide data.
3. Remove gesture listeners, expiry/momentum tokens, unused sentinel and artificial
   100svh blank stage. Search/Refresh/page changes load their requested full page.
4. Keep whole-library filters, per-tab context, revision-safe individual/bulk
   deletion, Undo and persistent Restore. Label Select this page explicitly:
   includes eligible offscreen rows on this page, never another page. Keep cap 24.
5. Display options stay in Settings; remove the duplicate global header shortcut.
   Remove Pi-hole UI bindings/control, omit its field when saving. Do not silently
   change legacy settings or rewrite historic Pi-hole observations. Backend code
   remains for compatibility/documentation, not a newly enabled feature.
6. Update readable applied filters/page-title orientation. Replace tests enforcing
   the superseded interaction with complete-page, jump/End/Find/focus/fallback,
   pagination/race and Delete/Restore checks. Verify Chromium/Firefox, offline gate
   and package. Physical AT/phone/participant claims remain separate.
7. Recheck home network before a fresh isolated Light/this-PC Deep pair. Record
   actual failed checks rather than hiding them; replay raw evidence and AI choices.

## Verification

No real reports were deleted or existing evidence overwritten for management tests.

- Final offline gate `.test-artifacts/checks-23f6794985/`: 660 Python passed,
  five Windows link-privilege skips, 97 deselections; 186 JavaScript tests;
  Ruff/159-file formatting and 21 shipped syntax checks. The revised History
  suite replaces obsolete gesture assertions with 22 complete-page/observer cases;
  the total differs from the earlier 195 JS, rather than claiming both contracts.
- Chromium/Firefox `.test-artifacts/history-viewport-browser-20261014-a/`:
  76 passed/two failed. Both failures were a synthetic fixture that marked an
  unreadable row but omitted warning text expected by the test. The row itself was
  present with preserved-files feedback. The fixture was corrected; both affected
  cases passed in `history-viewport-browser-20261014-b/`. No app security was weakened.
- The browser matrix covers 0/1/23/24/25/53 totals, initial full pages, End/scrollbar
  jumps, native text/focus, observer absence/failure, phone reflow, reduced motion,
  explicit page changes, filters, request failure/retry, selection scope, confirmed
  individual/bulk deletion, partial/stale outcomes, Undo and Restore after reload.
  Real screen-reader speech, physical phones and participant understanding remain
  pending; WebKit remains blocked by Windows policy.
- Two additional Settings compatibility tests passed for omitted legacy Pi-hole
  false/true fields. UI omission does not change saved choices.
- Offline package `.test-artifacts/package-e054c75113/`: six pages, 22 static
  assets, synthetic Delete/Undo/Restore/capability/usage; clean build/runtime
  dependency checks. All 99 installed app files matched source byte-for-byte.
- A final independent read-only agent review found no new material faults in the
  bounded-page controller, decorative observer, selection, stale-response guards,
  deletion/recovery controls and affected templates. This is a scoped code review,
  not proof that all application defects or usability barriers are absent.

## Fresh live pair

Windows still detected authorised WiFi `192.168.0.0/24`, this PC `192.168.0.216`.
Nmap 7.991 and local Ollama `llama3.2:3b` were ready. The new owned isolated folder
is `.test-artifacts/live-review-20261014-d/`; no Pi-hole or external CVE lookup.

Light `6b654e2a-e697-426c-857a-c5c210bc1d5e` finished in 390.0 seconds including
all eight explanation records: 8/10 checks completed, ten open features, seven
review items. Two `HOST_UNREACHABLE` addresses (`192.168.0.72` and `.154`) each
received two attempts; neither missing check was concealed or claimed passed.
Sleep/disconnection/refusal is possible, but no specific cause was established.

Deep `dec59fd1-1c3d-4014-9f24-e98fe19114a2` completed 1/1 checks in 529.3 seconds
including its five explanation records: fourteen open features, four informational
review items and no errors. Its expected `SELF_SCAN_LOCAL_ROUTING` warning remains:
checking this PC from itself does not establish what another device or the internet
can reach. No discovery stage was requested for this known-host Deep scan.

The fresh pair's `evidence-audit.json` passed raw XML replay for 141 service records
(120 Light, 21 Deep) and recalculation of all eleven findings. Thirteen accepted
AI records revalidated with zero rejected fields or fallbacks. Selected AI input
contained no recorded IP/MAC/hostname/range or raw XML. There were no missing raw
outputs for completed host checks; unsuccessful targets are not counted as replayed
successful checks. Validation checks factual constraints, not a guarantee that
every reader will understand the wording.

The real report pages passed eight Chromium profile/viewport cases at 320, 390,
768 and 1440 pixels without page errors or page overflow. `browser-results.json`
records exactly two scan submissions, both jobs retained after dashboard refresh
and automatic report navigation after analysis. Firefox was verified with synthetic
browser cases above, not with these live reports.

`integrity.json` confirms that pre-existing normal reports remained byte-identical.
The owned isolated backend stopped, and its port 47771 was confirmed no longer
listening. The normal backend was not stopped or restarted by this test. Its public
metadata now includes recovery/capability routes; served assets matched source.
Artifacts contain private network evidence and should not be published unredacted.

## Further recommendations (not all implemented here)

The [agent's researched follow-up](ui-ux-recommendations-20261014-followup.md)
compares complete pages, progressive cached append, virtualization and infinite
scrolling, with eighteen acceptance scenarios. Readable applied filters/current
page titles are implemented. Next useful work: make exact UUID references optional
technical details while retaining distinct report identity; measure management
feedback comprehension; run actual AT/phone/novice tasks; measure per-stage scan
time before adding more complex loading or aggressive probes. Existing recovery,
theme, provenance and stable-focus features are not described as missing.
