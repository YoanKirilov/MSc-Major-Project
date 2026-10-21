# Follow-up audit: remaining bugs and improvements - 18 October 2026

Status: investigation only, after [the preceding fixes](remaining-fixes-20261018.md).
No application fixes, deletions, commits or pushes were made in this pass. This is
a prioritised backlog, not a claim to have found every possible defect.

Subsequent implementation: [F1-F3 targeted fixes](issue-fixes-20261018.md). The dated
findings below retain their original audit state. The subsequent
[I1-I9 improvements record](improvements-20261018.md) distinguishes implemented
changes from remaining human, performance and hosted evaluation. Use
[the current verification index](verification-status.md) for status.

## Verification performed now

- Fresh offline gate `.test-artifacts/checks-13812120ad/`: **914 Python passed**,
  five Windows link-privilege skips, 150 opt-in cases deselected; **261 JavaScript
  passed**, all 28 syntax checks, lint and 188-file formatting passed.
- Fresh focused browser gate `.test-artifacts/audit-browser-20261018-b/`: **10
  cases passed**: actual response-policy enforcement, CVE normal/lost-response
  flows, visible control semantics and supporting-dialog keyboard/text-spacing
  checks. The shared header/accessibility fixtures exercised Chromium and Firefox;
  the CVE fixture itself launches Chromium, not both engines.
- Existing saved Light/Deep reports reopened in
  `.test-artifacts/live-review-20261018-b/verification-c876123111/`: both reports at
  320/390/768/1440 pixels, two private export previews, inventory views/reset and
  exact device return-focus passed. **Zero scan submissions**, no recorded page
  errors/overflow, normal existing reports and saved test evidence unchanged.
  The owned verification backend stopped. This was not another live scan pair.
- A read-only request to the normal running app confirmed the real CSP, nosniff,
  DENY framing, no-referrer and no-store headers. The earlier missing-header
  finding is not reopened as a current defect.
- Two additional synthetic JavaScript probes reproduced the edge cases below.
  Their HTTP replies were mocked; no device or public NVD request was sent.

No new network scans, name probes, AI generations, public NVD API compatibility
requests or dependency upgrades were performed. Ollama readiness was reported
available during saved-report preflight; that is not a fresh generation test.
No new hosted CI run was checked or triggered. Older test counts and the green
GitHub baseline do not establish a new hosted pass for the working tree.

## Confirmed findings, in recommended implementation order

### F1. Medium: CVE recovery can accept the previous lookup too early

Evidence: `app/static/js/cves.mjs:136-150` accepts any saved record for the service
when `onSaved` does not reject the snapshot. `createNoteState.apply` accepts an
equal revision. Recovery does not compare the record with the one visible before
the uncertain POST, nor associate it with the attempted lookup.

Reproduction: start with a saved record at revision 10; lose the response to a new
lookup; return the same revision-10 record from GET annotations. The synthetic probe
reported `disabledAfterLoss=true`, then `disabledAfterOldRecord=false` and
`recoveryHidden=true`, with the old record still displayed and revision still 10.
Thus the UI clears its pending uncertainty without evidence that the attempted
lookup finished. A second request could be attempted prematurely; the backend's
global lookup lock still protects against simultaneous work. This is not evidence
of corrupted references or a confirmed duplicate NVD submission.

Proposed fix: keep old references readable, but distinguish "earlier saved
references loaded; current lookup still unconfirmed" from a confirmed outcome.
Prefer a bounded lookup-operation identifier/status receipt; at minimum compare
the saved lookup's identity/signature with the pre-request record. A newer overall
annotation revision alone is insufficient: an unrelated title edit can advance it.
Handle intentional cache reuse explicitly rather than demanding a new CVE timestamp
for every successful POST. Do not automatically repeat a POST.

Acceptance: tests for unchanged old records, a newer revision caused only by a
title edit, new lookup results, valid cached receipts, stale/failed GETs and page
refresh; verify reference preservation, button state and keyboard recovery.

### F2. Medium: a repeated name lookup can leave a permanent waiting message

Evidence: `app/static/js/scan.js:980-995` sets "Looking for a name" and relies on
the note projection to replace it. `devices.mjs:364-370` returns early when the
saved name-record signature is unchanged. Timestamps from `schemas/common.py` have
one-second precision, so two quick identical lookups with mDNS disabled can have
identical content even though the saved annotation revision advances.

Reproduction with the real device component and note-state helper: render a saved
record at revision 10, run the controller's name-refresh handler, and return an
identical record at revision 11. Revision 11 is accepted, the button re-enables,
but the visible text remains "Looking for a name. The original report will not
change." No live name request was made. Successful persistence and signature-based
DOM preservation are not themselves a final operation-status update.

An initial isolated probe also forced a rejected stale receipt. That showed the
controller has no explicit final message for that branch, but alone does not prove
the full application's ordinary concurrent-snapshot flow leaves stale text: a newer
complete projection may already have supplied completion feedback. The accepted,
identical-record case above is the stronger confirmed reproduction.

Proposed fix: finish the operation's waiting state explicitly, independently of
whether saved evidence changed. Preserve newer notes, unchanged disclosure content
and focus. If necessary read the latest annotations once; do not repeat the name
probe automatically or weaken revision protection.

Acceptance: identical success records, new records and delayed/rejected receipts
must leave an accurate final outcome, with newer snapshots and keyboard focus intact.

### F3. Low: current evaluation instructions contradict newer evidence

`docs/evaluation.md:30` still says remote matrix runs are pending, whereas newer
records describe a green hosted baseline. Lines 43-44 describe an AI-outage/retry
browser experience that has since changed. The current quality traceability entry
also points to an older execution record. These are documentation consistency
issues, not a claim that current unpublished source passed hosted CI.

Proposed fix: give current instructions one status/verification index with dates,
commit/build identifiers and explicit unverified work. Preserve dated historical
evidence rather than rewriting it to look current.

Acceptance: distinguish baseline CI, unpushed changes, synthetic browser checks,
real scans, model readiness/generation and participant evaluation consistently.

## Recommended improvements, separate from reproduced bugs

### I1. High verification priority: test the critical flows in each actual engine

`browser_test_cves.py:106`, `browser_test_library.py:143` and
`browser_test_workflow.py:293` launch Chromium explicitly. These fixtures do not
become Firefox/WebKit tests merely because the matrix job has that name. Other
parametrised fixtures do exercise the selected engines; this is a specific coverage
gap, not a claim that the whole matrix is fake.

Parametrise the essential CVE, edit-conflict, refresh and recovery journeys, then run
the current changes in functioning hosted engines. Keep local OS code-integrity
protections enabled; a blocked WebKit launch is not a pass. Validate physical Safari
and assistive technologies separately.

### I2. Medium: retain useful CI failure artifacts and reduce redundant work

`.github/workflows/checks.yml` has no artifact-upload step. Some tests take
screenshots, but those files are not retained by this workflow. Capture bounded
synthetic failure screenshots, Playwright traces and JUnit summaries, and upload
them even when a job fails. Never upload real report data or bootstrap tokens.
Separate common offline/package checks from engine checks where this saves repeat
work, without silently dropping the supported OS/Python/browser contracts.
[Playwright's Python trace documentation](https://playwright.dev/python/docs/trace-viewer)
explains the available DOM/action/network diagnostics.

### I3. Medium: verify current CVE data coverage and make references actionable

The recent fixtures prove matching/recovery logic, not current public-database
compatibility. Add sanitised contract examples for un-enriched records, missing
applicability data, large responses, rate limits and incomplete related-product
coverage. Preserve explicit unavailable/unknown states; never treat missing
applicability as proof of no vulnerabilities.

NIST documents additive affected/SSVC data updates; the August affected-data change
applies to the history feed, not removal from the CVE detail endpoint. That is a
reason to validate the current contract, **not evidence that this app's `/cves/`
integration is broken**. See [NIST's technical updates](https://www.nist.gov/itl/nvd).

Consider a bounded, validated "Maker's advice" link when an NVD record supplies a
vendor-advisory reference. This is more useful to a home user than requiring them
to interpret a technical CVE alone. Validate external URLs, show the destination
and keep it user-initiated; never let AI invent a link or assert the device is
affected. NVD explains its reference tags on
[Vulnerability Detail Pages](https://nvd.nist.gov/vuln/Vulnerability-Detail-Pages).

### I4. Medium: measure understanding before further expanding AI wording

The stored Deep overview is now everyday wording and the self-scan limitation is
visible. The first-action paragraph is still long, and some deeper actions remain
generic. The AI chooses from reviewed wording; a model-selected sentence is not
independent evidence of readability.

Test whether nontechnical readers can answer: "What was found? Is this a confirmed
problem? What should I do first? What was not checked?" Then split the first action
into a short instruction plus optional explanation, and expand reviewed device/OS
instructions only where observed evidence supports them. Keep safety precautions
and uncertainties; do not remove caveats merely to shorten the page.

### I5. Medium: finish inclusive human testing and async-error checks

Automated focus/reflow tests passed but are not actual NVDA, VoiceOver, voice-input,
switch or physical-phone tests. Exercise both newly found delayed-result paths,
dialog focus return, 200%/400% true zoom, keyboard use and high-contrast settings.
Ensure one clear outcome is programmatically announced without stealing focus.
This follows [W3C status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
and [error-suggestion guidance](https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html),
not a claim of certified WCAG conformance.

### I6. Medium: benchmark larger JSON histories before choosing an index

`storage/library.py:34-54` enumerates and examines the whole library before slicing
the result page. The compact cache is bounded to 512 entries/8 MiB, not a persistent
search index. A 24-row UI page therefore does not bound search work; cache churn is
possible beyond its capacity. No current user-visible performance failure was measured.

Benchmark synthetic libraries below/above the cache size, including simultaneous
scanning, search, device inventory and cancellation. If needed add a rebuildable,
revision-aware compact JSON index or incremental metadata cache; retain authoritative
JSON, atomic writes, recovery and current locking. SQLite is not required for this
next step, and a database migration is not proposed here.

### I7. Medium: refactor narrow responsibilities behind existing contracts

The report controller is 1,278 lines and supervisor 1,080. Length alone is not a bug.
Extract report annotation/name/CVE coordination and scanner-stage coordination in
small tested steps. Replace `OllamaRuntime`'s direct use of
`provider._generation_lock` with a public preload/generation-slot interface, preserving
serialization, cancellation and bounded waits. Do not broadly rewrite working code
or delete compatibility connectors merely because their settings UI is hidden.

### I8. Low: improve unavailable-JavaScript/bootstrap guidance

The home button begins disabled at "Checking scanner..." and the dashboard has no
`noscript` explanation; My devices already provides one. Give the home/report pages
an honest no-JavaScript/loading-failure message with a safe next step. Keep the
existing external startup recovery. Static-preview redirection also assumes port
8765; document or support custom-port launch without weakening origin/session checks.
This is resilience/usability work, not evidence that normal startup failed in this review.

### I9. Medium: plan recovery-archive capacity and storage handoff

Recovery copies deliberately consume disk and fail closed at 1,000 entries/2 GiB.
Preserve Undo/Restore and no automatic purge. Add capacity-near-limit guidance and
an explicit, separately confirmed backup/retention workflow if permanent cleanup
is later requested. Deleted report copies remain private data. No deletion or
permanent-removal feature is authorised by this audit.

## Recommended next execution sequence

1. Add failing regressions for F1/F2, fix their state transitions, rerun the focused
   browser and offline checks. Preserve all factual reports and current UI layout.
2. Correct the current documentation/traceability index (F3).
3. Improve actual engine coverage and retained CI evidence (I1/I2), then verify a
   new published revision when pushing is explicitly requested.
4. Validate current public CVE examples and useful vendor-reference handling (I3).
5. Run inclusive novice/assistive-technology evaluation and apply measured content
   changes (I4/I5); benchmark before performance changes (I6).
6. Make small contract-preserving refactors and resilience/storage improvements
   (I7-I9). Keep Pi-hole deferred and keep local JSON storage.

No critical scanner, evidence-loss or scope-validation regression was identified
in the exercised paths. This does not certify their absence. Existing unreachable
devices, self-scan limits, selected-port coverage and rejected AI wording must stay
truthfully visible; they are not errors to hide.
