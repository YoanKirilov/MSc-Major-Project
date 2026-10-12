# UI/UX follow-up execution — 9 October 2026

Scope: implement the eight agreed follow-ups, preserving the current visual identity,
authorised scan flow, saved evidence, JSON storage and revision-safe annotations.
Use isolated synthetic/copied reports; do not run live scans or real provider calls.

1. Replace unknown loading counters with dashes; keep report sections unavailable until facts load.
2. Use one feature-specific review title across device buttons, result list, detail and tasks.
3. Keep matched comparisons with their device and share announcement/address matching rules.
4. Use valid button contents and announce meaningful progress changes separately from visual updates.
5. Restore bounded per-report, per-tab reading state without storing evidence, credentials or edit revisions.
6. Add compact, non-obscuring section navigation and an explicit collapse-all task action.
7. Put reviewed practical setting/page instructions beside the recommended action.
8. Explain Light/Deep by purpose first; retain exact coverage and authorisation details.

Verification: focused JavaScript regressions, synthetic browser tasks in Chromium/Firefox/WebKit,
the full offline gate and an installed wheel. Preserve previous failure histories and original report
bytes. Physical-device, screen-reader and nontechnical-reader sessions remain manual evaluation;
an automated test is not evidence of human comprehension or accessibility certification.

## Implemented changes

| Point | Implementation and regression |
| --- | --- |
| 1 | Unknown report metrics show dashes; the body starts hidden/busy. Controls inside it stay inert until restored layout/position is ready. A failed read offers a retry without turning unavailable facts into zeros. The browser retry test then distinguishes a genuine zero-service report. |
| 2 | `presentation.mjs::reviewItemTitle` supplies the same title to device links, review cards, details and tasks. Informational items name the feature; protocol/port distinguishes otherwise identical features. Saved titles and priorities stay intact. |
| 3 | Matched comparisons live inside About this device; the supporting section links there instead of repeating every device. `deviceResultEntries` supplies announcement matching for both checked results and unfinished-address placeholders. Unmatched claims stay separate and unverified. |
| 4 | Review buttons contain phrasing elements rather than headings/paragraphs. A separate polite status announces stage changes and bounded quarter milestones; visual elapsed/activity updates do not rewrite the live announcement every second. Deep checking still has no invented percentage. |
| 5 | `report-view.mjs` validates bounded, versioned per-report reading state in this tab's session storage. Search/filter/sort/selection, rendered disclosures, device limit and position restore after facts and layout load. Reload/back navigation restores the actual position rather than a stale section fragment. Blocked/full/corrupt storage is nonfatal. |
| 6 | Section navigation sticks only on sufficiently wide/tall screens; its measured height sets scroll padding without duplicating the offset in target margins. Enlarged navigation becomes nonsticky if it would occupy too much of the viewport. Tasks gain collapse-all; empty reports disable both bulk controls. A background note projection no longer reopens manually collapsed filtered groups; an explicit filter change reveals matching controls. |
| 7 | Reviewed feature settings, bounded web-page directions and saved check instructions are visible beside actions. Sign-in/encryption warnings stay with those directions; detailed provenance/evidence remains expandable. No device page is opened or checked automatically. |
| 8 | Light/Deep lead with their purpose: the network versus one device. A disclosure retains exact port coverage, duration/coverage limits and the existing authorisation boundary. |

These changes do not submit scans, refresh AI wording, fetch CVEs, change severity or
write evidence. Reading-state values never become API requests, edit revisions,
authorisation or HTML/selectors. Search and disclosure keys may contain local device
identifiers; this is best-effort local browser-tab state, not a backup or synchronised
preference. Closing/clearing the tab can remove it.

## Verification

- Focused new JavaScript tests pass for bounded/isolated storage, invalid or blocked
  storage, disclosure identity, navigation sizing, title identity and initial loading.
  Dashboard tests cover bounded announcement milestones and preserve existing recovery.
- All **24 new synthetic browser cases passed** across Chromium, Firefox and WebKit;
  `.test-artifacts/ui-followups-6d7fef4b49/`. Fixtures reject external requests and
  scanner/provider calls, and assert original report bytes remain unchanged.
- Fresh offline wheel verification passed **six pages, 16 assets and fictional
  demo read/create/reopen**; `.test-artifacts/package-b1917395b0/`. Runtime and build
  environments both passed `pip check`; dependency wheels came from the local cache.
- Final `scripts/check.py --browser --browser-engines chromium,firefox,webkit`
  passed **688 Python/browser tests and 102 JavaScript tests**. One live-provider
  test was deselected. Ruff lint/format and all **15 module syntax checks** passed;
  `.test-artifacts/checks-131d42025f/`. This fresh run used the finished source and
  updated contracts throughout, not an intermediate snapshot.
- Final synthetic screenshots were spot-checked at mobile/desktop widths. This is
  a visual development review, not a physical-phone or participant evaluation.

Early focused runs exposed incorrect new test expectations/selectors (coverage is
"1 of 1 discovered", task titles are outside the disclosure summary, and mobile
details share finding IDs with action controls). Those tests now target the correct
structures without weakening uncertainty, evidence-integrity or offline guards.
Existing CVE/library tests also assumed refresh discarded open disclosures/searches.
Their new assertions verify restoration and explicitly clear/open controls when needed;
the saved-reference, stale-snapshot, conflict and evidence checks remain intact.
The synthetic workflow likewise now asserts that its opened device remains open after
nickname editing/reload; the stale-cache regression pins the new module query version.
All **nine workflow/dashboard integration cases passed** in
`.test-artifacts/ui-workflow-855270ce4a/`; all **12 selection/focus cases passed** in
three engines in `.test-artifacts/ui-selection-86514355cd/`.
Loading-to-reading hand-off and filtered-task collapse were tightened during review.
The initial full run overlapped those adjustments and is not the final verification
record. Failed and intermediate artifacts were retained; the fresh complete gate is
the release condition and passed. In particular, the two intermediate full runs
loaded the old workflow/cache assertions before they were corrected; neither is
reported as a passing gate. The final run has no failing cases.

No new live scan, real Ollama/NVD/Pi-hole call, normal-backend restart or deletion of
user reports ran. Physical phones, actual browser zoom, screen-reader evaluation,
Ubuntu and nontechnical readers remain manual verification, not claimed completed.
