# Final wording and supporting-layout follow-up — 12 October 2026

Status: implemented and verified. Application presentation, offline/full-browser
gates, installed-package checks and the live-report review passed. Light's one
unreachable device remains an honest coverage limitation, not a completed check.

## Execution plan

1. Remove duplicate original/previous rule-based explanations and steps from the
   per-finding interface. Render the final accepted explanation and action wording
   once, including reviewed fallback text if AI is unavailable. Preserve original
   findings, snapshots, evidence and validation data in JSON/export. Keep honest
   wording-source notices and useful technical evidence, not duplicate explanations.
2. Arrange bottom supporting disclosures side-by-side in one desktop row. Use
   consistent cards/spacing, wrap at smaller widths, and give open content a wider
   row so long text is not squeezed into narrow columns. Retain native disclosure
   keyboard behaviour, IDs and saved reading state; no fake tab roles.
3. Widen the shared header/main/footer maximum from 1240 to 1360 CSS pixels using
   one design token. Keep short prose lines bounded and mobile padding unchanged.
4. Shorten technical disclosure labels, make filtered review-count feedback a
   concise polite status message, and make zero-task/no-match wording actionable.
   Keep permission/password precautions and uncertainty visible, not hidden here.
5. Add focused JavaScript and Chromium/Firefox/WebKit regressions for final-only
   wording, evidence preservation, closed supporting-row geometry, opened content,
   keyboard/reload behaviour, narrow/enlarged layouts and status feedback.
6. Run new authorised Light home-range and Deep this-PC scans after the changes.
   Use fresh isolated JSON folders, retain raw XML, validate Ollama against selected
   facts, and reopen the reports across browsers without additional scan/edit
   submissions. Preserve normal reports/backend and leave Pi-hole/CVE-provider
   requests disabled. Finish an offline/full-browser gate and update this record.

## Research basis

Optional supporting information uses native disclosures, consistent with the
[GOV.UK details pattern](https://design-system.service.gov.uk/components/details/).
Important decisions and precautions stay in the main explanation. The desktop row
must adapt to narrower/enlarged displays without losing controls or forcing horizontal
page scrolling, following [W3C reflow guidance](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html).
Only concise filtering counts are announced, following
[W3C status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).
Shorter labels follow [W3C clear-word guidance](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o3p01-clear-words/).
These are design references, not a standards-certification claim.

Scope confirmed by local adapters: home `192.168.0.0/24`, this PC `192.168.0.216`.
Virtual-machine adapter ranges are excluded. Normal backend PID 14912 on 8765 is
not restarted, authenticated to or replaced by these checks. Existing staged work
belongs to the user and is preserved; no Git index/commit changes are authorised.

## Verification and remaining limits

Implementation and executed results are recorded below. The previously
investigated intermittent Windows transport-close warning is not marked fixed.
Actual reader, assistive-technology, physical-phone and Ubuntu/lab studies remain
separate from an editorial novice review and automated browser checks.

## Implemented changes and early verification

The four presentation steps are implemented. Duplicate current/original step
disclosures, original-explanation disclosures and earlier inline guidance versions
are no longer rendered. JSON/API/exported evidence is retained; accepted wording
and reviewed fallback still work. The optional details now use the shorter label
“Sources and technical details.” Model provenance and research references remain
optional; coverage limits and practical safety instructions remain visible.

Five supporting options (six when unmatched announcements exist) share one desktop
row. Their native disclosure cards have consistent borders/spacing. Open panels
span the available row with prose capped at 75 characters; phone/tablet layouts
wrap naturally. The shared shell now uses `--page-max-width: 1360px`. Paragraph
alignment preferences, native keyboard interaction and existing report IDs are kept.

Review-count feedback is a concise polite status region. A zero-task report no
longer invites opening nonexistent headings; a no-match filter explicitly says
to choose All statuses. These are reading/feedback changes, not saved action edits.

Six new focused browser cases passed across Chromium/Firefox/WebKit in
`.test-artifacts/final-layout-focus-20261012-47ab2e/`: desktop row/width geometry,
native keyboard/open-panel/reload behaviour, 320/390/768-pixel and enlarged-text
reflow, final-only explanations and unchanged JSON rules/history/AI output.
The finished-source offline gate passed **602 Python and 111 JavaScript tests**
with lint, formatting for 146 Python files and syntax for all 15 JS modules in
`.test-artifacts/checks-124ea0530d/`. The full three-engine gate and live-pair results
will be recorded separately below, not inferred from these isolated checks.

Offline installed-package verification passed in
`.test-artifacts/package-3df06ab409/`, using the existing wheel cache with no index
access and fresh builder/runtime environments. Dependency checks, six page routes,
all 16 static assets and synthetic demo create/reopen passed. The complete 91-file
app payload matched source file names and bytes exactly. This did not install over
the normal app environment or run Nmap/provider requests.

## New live pair

Scans saved in `.test-artifacts/final-layout-live-20261012-183ea6/`:

| Result | Light home range | Deep this PC |
| --- | --- | --- |
| Scan ID | `09ba210c-bca9-4a68-b65a-0d07dbd3728e` | `98b3842a-9b2d-46ed-99e0-5d39c5d540dd` |
| Device checks | 9 of 10 discovered completed | 1 of 1 selected completed |
| Answering features / review items | 12 / 8 (four Low, four informational) | 14 / 4 informational |
| Duration including wording | 291.2 seconds | 535.5 seconds |
| Accepted AI records revalidated | 8 | 5 |

Light retained one failed device check at `192.168.0.226`, reason
`host_unreachable`, after two bounded attempts. It may be asleep, disconnected or
not responding; no cause or security verdict is established. This is an observed
coverage limitation, not a reason to fake successful completion or erase its card.
The report must display the unfinished count and its existing retry option. Deep
had no scan errors and retains the expected local-self-routing warning: checking
this computer does not establish other-device/internet access.

Raw XML/rule replay matched **156 service records and all 12 findings**. All **13**
accepted AI records revalidated, with zero rejected fields. One Light wording block
retained reviewed fallback (`not_simpler`); that final text remains available even
though duplicate original-version disclosures are gone. Selected AI inputs contained
no IP/MAC/hostname/network-range/raw-XML identifiers. Light recorded four mDNS
announcements. No Pi-hole or external CVE lookup was requested.

Both pages recovered their immutable targets/progress after refresh and automatically
opened the saved report after wording finished, with exactly two scan submissions
and no page errors. The owned scan backend stopped after completion. Original and
copied report hashes were unchanged; normal history was not replaced or augmented.

## Actual-report UI verification

The finished read-only viewer passed **16 engine/profile/viewport combinations**
in `browser-check-1bfc23dc/` inside the live folder: Chromium 320/390/768/1440 and
Firefox/WebKit 390/1440. Closed supporting cards shared one desktop row; visible
summary targets were at least 44 by 44 pixels, with no horizontal page overflow.
Header/main/footer widths were 1360 pixels on the desktop checks. Report reading
alignment, grouped device evidence, review-device filtering, selection/reload,
exact-IP search, history reopening and Run again setup still worked.

All **12 actual review-item explanations** were captured and checked for final-only
wording; no original-version/earlier-inline-guidance disclosures remained. The main
meaning, independent action controls, purpose/help and uncertainty sections remain.
Desktop supporting-row and mobile detail screenshots were visually spot-checked.
Light's visible headline was “Scan finished; 1 device could not be checked.” with
the retry action available and the failed device explicitly not assessed.

The first viewer attempt measured a summary inside a legitimately hidden optional
announcement section and stopped on a missing bounding box. That harness failure
is retained in `browser-check-ce67cecf/`, not counted as a pass. The corrected
visible-control check passed without changing application source.

The final viewer recorded **zero page errors and zero extra scan/edit submissions**.
All 16 served JS/CSS assets matched source bytes with `no-store`. Original, copied
and reopened live report hashes were unchanged. Owned scan/viewer backends were
stopped; inspection found only normal PID 14912 on 8765, with no listener on 8766.
Neither missing host coverage nor the reviewed fallback was hidden to obtain a pass.

## Finished-source quality gate and handoff

The final full three-engine gate passed **732 Python/browser tests and 111
JavaScript tests** in `.test-artifacts/checks-164e0c7bb6/`, with one optional
real-provider test deselected. Ruff lint, format checks for 146 Python files and
syntax checks for all 15 JS modules passed. Actual local Ollama behaviour is
evidenced separately by the live pair and its saved/revalidated wording.

No application behaviour changed after the focused tests; the supporting template
block was only indented before packaging/live checks. No source changes followed
the package check or live-report viewer; only evidence documentation was completed. Existing staged
Git work was preserved, with no commits/index changes or normal-data writes.
Refresh an existing report page to see the new UI. Fresh test scans remain in the
isolated test folder rather than being silently added to normal history.

Retry the unfinished address only when it is available and still authorised; do not
erase its failed-check evidence or label it safe. Real-reader, assistive-technology,
physical-phone and Ubuntu/lab evaluation remain open. The earlier intermittent
Windows transport-close warning did not appear in these live/viewer logs but is not
claimed repaired. Pi-hole and actual external CVE-provider evaluation remain deferred.
