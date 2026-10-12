# UI/UX implementation and verification — 8–9 October 2026

## Scope and execution order

This implements the presentation changes in the [28-item review](ui-ux-review-20261008.md).
That review is historical baseline evidence, not a description of the revised interface.
The dark/teal identity, FastAPI backend, local JSON storage, required Ollama workflow,
factual findings and revision-safe notes remain. No live scan, identification request,
Pi-hole connection, NVD query or real Ollama request was needed for this UI work.
The affected quality requirements are Q03/Q04/Q06/Q07/Q09/Q11/Q12/Q13; see the
[quality traceability follow-up](quality-traceability.md#presentation-follow-up--9-october-2026).

The development sequence was:

1. Reproduce internal checklist/search geometry and lost keyboard focus with synthetic reports.
2. Repair controls, stable selection and immediate mobile detail placement.
3. Standardise device cards, contextual information, shared navigation and forms.
4. Reorder the report, separate search scopes and expose the complete review checklist.
5. Extract cohesive rendering/editor components and consolidate responsive styles.
6. Verify offline, in browsers and in an installed wheel; preserve original scan JSON.

Parallel work used separate file ownership for shared styles/forms, device/CVE components
and new browser regressions. Integration also fixed faults uncovered by the new checks.

## Finding-by-finding implementation

| Finding | Change in the application | Verification focus |
| --- | --- | --- |
| UI-01 | Checklist controls occupy the instruction column, not the 24px number column. | Child/select containment at narrow and desktop widths. |
| UI-02 | Finding buttons retain their DOM identity and selection state; unchanged details are projected in place. | Enter activation, focus outline and resize preservation. |
| UI-03 | Below 880px the detail panel follows the selected finding directly; desktop retains master/detail layout. | Selected row and panel measured in the same browser frame. |
| UI-04 | Flexible search fields reserve space for clearing; clearing returns focus to that input. | Input/button bounds and text-spacing overrides. |
| UI-05 | Priority badges cannot shrink or wrap within a word; long device context wraps separately. | Medium badge stays on one line beside long names. |
| UI-06 | Buttons and disclosure rows use padded, generally 44px targets with consistent gaps. | Disclosure rectangles and narrow-screen control placement. |
| UI-07 | One device-card boundary contains identity, expandable content and its action footer. | Sparse/rich/unfinished cards share the same anatomy. |
| UI-08 | Nickname/identification actions and both Deep rerun choices use secondary styling. | Action hierarchy and contextual association. |
| UI-09 | Collapsed cards show name/nickname, address, name qualification, type uncertainty, check status and counts. | Unknown, historical and conflicting identities remain qualified. |
| UI-10 | Name/model/manufacturer/source/confidence information is available inside each device's plain-language detail. | Recognition evidence can be reached without the technical table. |
| UI-11 | All answering features have plain labels inside their device; there is no five-feature cutoff. | Thirteen-feature fixture and service-evidence qualifiers. |
| UI-12 | Counts identify their population: completed checks, discovered/selected addresses, usable results and search matches. | Failed addresses are retained but excluded from name-coverage totals. |
| UI-13 | Compact overview presents date/profile, completion and one set of metrics. | Overview bounds and removal of duplicated metric cards. |
| UI-14 | Report order is overview → first task → devices → review items → complete checklist → supporting information. | First-review and recognition shortcuts; all sections remain reachable. |
| UI-15 | Generic AI provenance/original guidance moves behind supporting disclosures; critical limits stay visible. | Original text/evidence retained; self-check warning not duplicated. |
| UI-16 | Review titles identify the feature; context wraps rather than being silently truncated. “Port” is defined consistently. | Honest plain-language labels and full address/context access. |
| UI-17 | Every finding action appears in the complete checklist, grouped by review item; all controls can be expanded. | Global count equals reachable tasks; no three-group/first-action cutoff. |
| UI-18 | A short visible “Your review status” label replaces repeated instructions; accessible context still names the device/action. | Independent action identity, local save status and matching duplicate controls. |
| UI-19 | Device and review-item searches are independent; priority counts follow review search. Task status filters hide whole task rows only. | Search scope, reset focus, empty filters and detail recommendations unaffected. |
| UI-20 | Matched announcements and earlier comparisons appear inside their device; unmatched announcements remain separate. | Advertisements never become evidence of an open feature or verified identity. |
| UI-21 | CVE eligibility/saved-result status is concise; research, privacy, evidence and action are collapsed. | Opening a disclosure submits no lookup; explicit lookups retain revision guards. |
| UI-22 | All pages share NetGuard navigation, footer, main target and meaningful titles. | Six page types, current-page navigation and keyboard bypass. |
| UI-23 | Shared field, focus, secondary-button, error and spacing styles apply to Settings/history/report forms. | Form reflow and token contrast measurements; not conformance certification. |
| UI-24 | Labelled modal editors replace nickname/title prompts. Settings/history fields are grouped with local errors and retained drafts. | Save/cancel, focus return, conflict, validation and read-only automatic scope. |
| UI-25 | Components distinguish loading, empty, no match, failed checks, unavailable AI and save failure. Saved-report reload has an explicit recovery action. | Synthetic state fixtures and evidence remaining accessible. |
| UI-26 | Shared skip link, narrow status regions, native disclosures and explicit modal focus cycling replace broad live-region updates. | Keyboard bypass/selection/dialog tests; manual screen-reader evaluation remains. |
| UI-27 | Device details default closed at every size; sorting/search/jump links and explicit Show more preserve access to all results. | 0/1/100-device fixtures plus a copied 24-address saved report. |
| UI-28 | Device rendering, stable finding lists and text editing are separate modules; CSS is organised by component and responsive state. | Actual module tests, component geometry, task flows and static/package reachability. |

Cards intentionally have natural expanded heights. Content is not cropped to force
equal heights, and no new database, model-generated identity or port-only CVE matching
was introduced.

## Integration faults also repaired

- The complete-task render cache now includes scan/analysis state, coverage and the
  displayed report overview. A zero-finding report can no longer retain an earlier
  incomplete-state next step after its saved analysis changes.
- Device details preserve nested disclosure state and focus across nickname updates.
  Explicit recognition opens the requested card; a user's collapse remains respected
  during background refreshes and after filtering.
- Page-footer CSS is scoped to `.site-footer`. It no longer changes a device action
  footer into a wrapping column on mobile. Long local error messages wrap without
  clipping or hidden overflow.
- The editor traps Tab/Shift+Tab at its boundaries. If a renamed device disappears
  from the active search, closing restores focus to device search rather than the body.
- Package data includes the shared header/footer templates in `templates/includes/`.
  Updated browser tests use the new editor/search/disclosure contracts while retaining
  stale-response, revision-conflict, escaping and evidence-integrity assertions.
- The Settings network-mode options are concise, with their full explanation beside
  the control. This removes native WebKit select overflow at 320px without hiding
  page overflow or clipping surrounding instructions.
- The shared skip link has explicit `tabindex="0"`, preserving ordinary Tab access
  when WebKit's default keyboard preference otherwise skips links. No positive
  tabindex or changed security policy is needed. Snapshot tests await initial data;
  refresh-during-scan and independent-tab recovery checks remain in the workflow suite.

## Verification record

Final combined gate passed on 9 October:

- **664 Python tests passed, one live-provider test deselected**, including synthetic
  browser coverage in Chromium, Firefox and WebKit. Artifact directory:
  `.test-artifacts/checks-114d5b235a/`. The pytest phase took 535.30 seconds.
- **93 JavaScript tests passed** across seven suites, including 23 actual report
  renderer tests and 18 device/CVE component tests. Ruff lint/format and all **14**
  module syntax checks passed. Template/static reachability and evidence-integrity
  regressions are included; passing these does not prove every individual function is used.
- Responsive checks include 320–2560px widths, portrait/landscape and narrow-screen
  text enlargement. The new component tests cover checklist/control containment,
  focus preservation, mobile selection placement, independent filters, modal edits,
  historical/conflicting names, AI outage and 0/1/100-device synthetic states.
- Separate copied-report audits passed **25 measured states each in Chromium and
  WebKit**, with no page errors, horizontal page overflow, external requests or
  mutation requests. Original report bytes were unchanged. They used isolated copies
  of saved Light/Deep reports, not new live scans. Private artifacts:
  `.test-artifacts/ui-ux-postfix-20261008/` and
  `.test-artifacts/ui-ux-final-webkit-20261009/`.
- A final fresh installed wheel passed **six rendered pages, 15 static assets** and
  fictional demo creation/reopening, with dependency consistency checked and only
  local pinned wheels used. Artifact directory: `.test-artifacts/package-8b658223fb/`.
  No existing app environment or report folder was replaced.

Failure history is retained: the earlier combined gate in
`.test-artifacts/checks-25ea6fca02/` had 660 passes and four failures. Two reproduced
the same WebKit Settings overflow; one exposed skip-link keyboard behaviour, and
one navigated before initial synthetic setup requests finished. Targeted WebKit
regressions passed after correction, followed by the successful complete gate above.
Actual refresh-during-scan, stale-response, write-conflict and unchanged-evidence
assertions were retained rather than excluded to obtain a passing run.

Use the repeatable offline runner:

```powershell
$env:BROWSER_CHANNEL = ''
python scripts/check.py --browser --browser-engines chromium,firefox,webkit
```

This opts into synthetic browser workflows, not live network/provider tests. The
runner creates its own artifact directory. The new suites also prohibit external
browser traffic and verify saved scan bytes; do not point tests at normal report data.

Private screenshots and copied home-report observations are in ignored
`.test-artifacts/` directories. Do not publish them without redaction.

## Remaining evaluation, not hidden implementation defects

Automated checks establish the tested interaction contracts, not that every home user
understands the interface or that the site is WCAG-certified. The following remain
separate evaluation work:

- Physical Android/iOS devices, on-screen keyboards and real browser 200%/400% zoom.
- Manual screen-reader announcements, heading navigation and full contrast/target audit.
- The intended Ubuntu installation and remote CI execution.
- A nontechnical-reader study comparing device-first and priority-first entry, recognising
  an unknown device, interpreting incomplete checks/answering features and finding all
  remaining checklist actions. Marking Checked must not be interpreted as verified safety.

The [reader-study protocol](evaluation-session.md) supplies the next tasks. Collect
actual participant results before claiming comprehension improvements; do not infer a
pass rate from automated browser tests or an assistant walkthrough.
