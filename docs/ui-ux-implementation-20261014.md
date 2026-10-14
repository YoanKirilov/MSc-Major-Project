# UI/UX implementation — 14 October 2026

Execute the [research brief](ui-ux-recommendations-20261014.md) and
[live findings](live-check-20261014.md) without changing scan evidence, permissions,
the empty initial History view, one-at-a-time reveal or 24-report pages.

## Sequence and acceptance gates

1. UX-02: reconcile running-job rows by ID, retain action nodes and pending
   cancellation, move focus only when its job disappears. Test changed polls,
   failure, cancellation and disappearance with synthetic jobs.
2. UX-03/04: identify reports in selection/confirmation by title, type, recorded
   time, target and reference. Keep UTC date filtering explicit and show its
   matching UTC day beside the local date. Test midnight, DST and invalid dates;
   never rewrite timestamps or infer a legacy timezone.
3. UX-05: stay on Settings after saving, track only scanner-form changes, offer
   deliberate discard and warn on leaving with edits. Display choices remain
   immediate and separate; failed saves keep input.
4. UX-06: add authenticated, bounded recovery listing and Restore using existing
   admission/path/revision guards. Account for active and recovery files separately;
   include recovery in offline checksum backups. No purge or permanent deletion.
   Test reload recovery, damaged receipts, refused overwrite and private storage.
5. UX-08/09: add a concise truthful wording-source label at each review item;
   retain submitted History filters/page per tab with expiry. Resume only after
   intentional scrolling, clear selection, and correct a disappeared final page.
6. Live wording/UX-10: say devices were found, not identified; make the known
   self-computer role visible without pretending to know its remote device type.
   Retain existing name-refresh diagnostics/help and factual uncertainty.
7. UX-11: document small shared component/state contracts; add opt-in device theme
   while preserving explicit Light/Dark and device reduced-motion priority.
8. UX-01/07/10: expand automated keyboard, small-screen, text-spacing, forced-colour
   and preference checks, and prepare actual screen-reader/novice tasks. Physical
   phones, assistive-technology speech and participant comprehension cannot be
   substituted by headless tests and remain pending until actually performed.
9. Run offline Python/JavaScript/lint and affected Chromium/Firefox tests. Verify
   packaging if assets/endpoints change. Recheck the authorised home scope before
   a fresh isolated live Light/Deep pair; audit saved facts against raw XML and
   accepted AI choices. Preserve normal reports and record limitations separately.

## Execution evidence

| Brief item | Implemented / remaining |
| --- | --- |
| UX-02 | Keyed job rows retain Open/Cancel controls, pending cancellation and keyboard focus; failure feedback persists; focused disappearance has an explicit destination. |
| UX-03 | Selection and confirmation include type, zoned recorded time, target and unique reference; revision/selection guards are unchanged. |
| UX-04 | UTC filters are explicitly inclusive; rows show the matching UTC date, and all date helpers show a timezone. Midnight/DST/invalid legacy tests preserve stored timestamps. |
| UX-05 | Stay on Settings with durable success, server-only dirty state, discard confirmation and leave warning. Preferences apply immediately with storage feedback. Further edits while saving are not claimed saved. |
| UX-06 | Authenticated recovery listing (24/page), metadata/size and revision-safe Restore after navigation. Managed `.trash` evidence/receipts join checksum export; active/recovery usage is separate. No permanent deletion or purge. |
| UX-08 | Per-item wording-source control opens existing source details by keyboard; safety-verification and user Checked limits remain explicit. |
| UX-09 | Bounded, expiring private session context restores submitted filters/page only after deliberate reveal. Selection never resumes; disappeared last pages correct once. |
| UX-11 | Opt-in device theme, forced-colour states, component/state reference; Dark/Light and device reduced motion retain priority. No new framework. |
| Live wording | Devices are found rather than identified; known self-computer role replaces an unknown type in the summary. Duplicate feature notation moves into technical details. Name-refresh help/diagnostics remain bounded and truthful. |
| UX-01/07/10 | Automated keyboard/reflow/text-spacing/forced-colour gates expanded. Actual AT speech, voice/switch/physical devices, true browser zoom and novice comprehension remain pending; the study protocol is prepared in `ui-components.md`. Resume/onboarding expansions await reader evidence. |

### Gates and failed attempts

- Final offline gate: `.test-artifacts/checks-faa20e7b53/`, 658 Python passed,
  five actual Windows link-privilege skips, 96 deselections; 195 JS; Ruff/158-file
  formatting and twenty syntax checks. No live probes/providers in this gate.
- New recovery/API/backup cases: five passed, including authenticated listing,
  24-item bounds, corrupted/changed archives, no unsafe traversal and restoring a
  checksum backup's recovery copy in a new folder.
- Browser attempt A failed at setup because its parent basetemp directory was
  missing. Attempt B: 53 passed/seven failed; fifty older History cases passed.
  Failures were new ambiguous locators, CSP-blocked inline test styling, a missing
  status stub caught by the offline guard, and a Firefox beforeunload-message
  assertion. These were fixed in the harness, not by weakening app security.
- Focused retest C: `.test-artifacts/ux-reliability-browser-20261014-c/`, ten passed
  in Chromium/Firefox. Report source/keyboard/320-pixel text-spacing/forced-colour
  checks: `.test-artifacts/ux-report-browser-20261014-a/`, two passed. These do not
  substitute for listening to a screen reader or testing a real phone.
- An intermediate offline run failed its old hard-coded asset-version assertion
  after cache stamps were updated; the final gate above passed the new stamps.
- Final package: `.test-artifacts/package-95f3b066f5/`, six pages/21 assets,
  authenticated recovery/capability/usage and synthetic report Delete/Restore;
  clean dependency checks using the offline wheelhouse. The final wheel was rebuilt
  and reinstalled only in that owned test environment after the last UI edits;
  installed checks passed again and all 98 app files matched source. The setup-tools
  indentation edit passed its ten Node tests. An older-backend storage-display
  guard passed two additional Chromium/Firefox tests in
  `.test-artifacts/ux-storage-compatibility-20261014-a/`.

### Live verification

The fresh pair is in `.test-artifacts/live-review-20261014-c/`, Light
`67740045-1c75-4b7a-ad51-328b55d4ff02`, Deep
`8b42330f-dc97-43d1-8597-3e06c24a21e4`. [The final live record](live-check-20261014-followup.md)
documents Light 9/10 with one unreachable address after two attempts and Deep 1/1.
Both finished enrichment and AI; 156 service records/eleven findings replayed,
thirteen AI records revalidated, zero rejected fields/fallbacks. All eight actual
Chromium report/profile viewport cases passed; refresh retained both jobs and only
two scan submissions occurred. Normal report hashes were unchanged and the owned
backend stopped. Normal port 8765 still lacks the new
recovery/capability routes while serving current assets: restart that backend task
after any normal jobs finish; the isolated backend already includes the new code.
