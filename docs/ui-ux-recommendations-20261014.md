# UI/UX recommendations for NetGuard - 14 October 2026

This is a source review and current primary-source research requested alongside
the separate live Light/Deep checks. It recommends work; it does not implement
changes or claim live reproduction. No scanner, provider, browser, server or
report-management operation was run by this review agent. Only this document was
created. No applicable `AGENTS.md` was found in the repository or ancestor paths.

The highest-value next work is to evaluate the custom History interaction with
assistive technology, preserve focus during running-job updates, identify reports
unambiguously before deletion, and make date and recovery behaviour easier to
understand. An additional visual redesign is a lower priority than these tasks.

## Scope and evidence

Reviewed the Home, report, Saved reports and Settings templates, shared shell,
appearance CSS and their JavaScript controllers/helpers. The current contracts
come from [architecture-current.md](architecture-current.md) and
[report-management-20261013.md](report-management-20261013.md). Older UI records
were used for context; superseded controls are not recommended as missing features.
File locations below describe the source on 14 October; function/selector names
remain useful if later changes move the line numbers.

Evidence is separated as follows:

- **Source finding:** directly visible implementation behaviour, with no claim
  that a person has encountered the resulting problem.
- **Evaluation risk:** plausible difficulty requiring browser, assistive-technology
  or participant evaluation before severity or conformance can be concluded.
- **Product opportunity:** a proposed improvement with benefits and costs, not a
  current defect or mandatory standard.

The user's empty initial History, one-by-one reveal and maximum 24 reports per
page remain product requirements. Standards do not prescribe those choices.
Recommendations below preserve them. Reintroducing a repeated **Show next report**
button or making initial reports appear automatically would need a separate
product decision, not a claim that a standard requires that design.

## Relevant models and current design-system patterns

This is a deliberately bounded survey of established models and currently
maintained design systems, not an exhaustive census of all UI/UX practice or proof
of which patterns are most popular. Publication age is not a reason to discard a
useful model, and use by a large vendor does not establish suitability for NetGuard.

| Model or pattern | Application to NetGuard | What it does not establish |
| --- | --- | --- |
| Nielsen's usability heuristics | Visible scan state, familiar labels, consistent actions, error prevention and recovery, recognition of a saved device/report rather than remembering an address. | A heuristic inspection does not demonstrate that novices can complete a task. |
| Progressive disclosure | Keep the first useful action visible; reveal technical evidence, exact ports and model details when requested. | Hiding primary navigation or essential precautions is not automatically helpful disclosure. |
| Task-oriented navigation | Choose scope, run/check progress, understand evidence, record a review and return later. | Every review need not become a fixed wizard or mandatory checklist. |
| State-based feedback | Explicit idle, waiting, running, unavailable, unfinished and finished states; durable feedback for actions. | A spinner or percentage alone does not explain progress or prove a device answered. |
| Reversible actions | Named deletion confirmation, bounded selection and recoverable reports. | Undo availability in one open page is not a complete recovery experience. |
| Human-AI interaction guidance | State what generated wording contributes, its limits and its source; make useful evidence inspectable. | An AI label or accepted wording check does not prove an observation is true. |
| Responsive and accessible interaction | Native controls, meaningful focus, reflow, visible states and user preferences. | An accessibility setting or automated pass is not WCAG conformance. |
| HEART goal-to-metric mapping | Measure successful safe review, retrieval and recovery, with user confidence calibrated to the facts. | More clicks, time on page or scans are not necessarily better outcomes. |

These applications are review inferences. The underlying primary references are
[Nielsen's heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/),
[progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/),
[GOV.UK task-list guidance](https://design-system.service.gov.uk/components/task-list/),
[Carbon notification guidance](https://www.carbondesignsystem.com/building-blocks/core/components/notification/guidelines),
[Microsoft's HAX guidelines](https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/)
and the [original HEART research](https://research.google/pubs/measuring-the-user-experience-on-a-large-scale-user-centered-metrics-for-web-applications/).
Carbon's currently published AI framework explicitly supports visible AI presence
and contextual explainability; this is a relevant current pattern, not a reason to
copy IBM's branding or add chat. [Carbon for AI](https://www.carbondesignsystem.com/building-blocks/foundations/carbon-for-ai).

## Useful behaviour already present

Home already distinguishes network-wide Light from one-device Deep, shows saved
target context, separates scan stages from time estimates, includes elapsed time
and app-connection context, and supports per-tab jobs. The report already has a
first action, section links, device/priority/search filters, technical disclosures,
per-action review status, uncertainty language and per-tab reading restoration.
Settings separates browser display choices from saved scanner configuration and
retains input on save conflicts. History already has labelled pagination,
shown-only selection, safe-default native confirmation, partial-result feedback
and immediate Undo. Theme, text-size, focus styling and reduced motion exist.

Preserve these behaviours while improving the gaps below. The dated verification
records are useful evidence of specific tested scenarios, not a current full
accessibility audit or a guarantee across all browsers and devices.

## Prioritised recommendations

Priority **P0 evaluation** means resolve evidence needed for an accessibility or
usability claim; it is not a declaration of a proven failure. **P1** is the next
implementation/review batch. **P2** follows after the core flows are evaluated.
Effort S/M/L is an approximate relative scope, not a delivery estimate.

| ID | Priority | Recommendation | Evidence type | Effort |
| --- | --- | --- | --- | --- |
| UX-01 | P0 evaluation | Test History reveal with actual assistive technology and alternate inputs | Evaluation risk | M |
| UX-02 | P1 | Preserve keyboard focus when running-job status changes | Source finding / reproduction needed | S-M |
| UX-03 | P1 | Give selection and deletion distinct report identities | Source finding | S |
| UX-04 | P1 | Explain and align displayed dates and date-filter boundaries | Source finding | S-M |
| UX-05 | P1 | Make settings save success and unsaved changes persistent and clear | Source finding / product opportunity | S-M |
| UX-06 | P1 | Plan a recovery browser and complete storage accounting | Documented limitation / product opportunity | L |
| UX-07 | P1 evaluation | Check focus, text spacing, forced colours and physical-device operation | Evaluation risk | M |
| UX-08 | P2 | Show concise wording provenance at the review item itself | Source finding / product opportunity | S |
| UX-09 | P2 | Restore History search context when returning from a report | Source finding / product opportunity | M |
| UX-10 | P2 | Evaluate task resumption and contextual help with real readers | Product opportunity | M |
| UX-11 | P2 | Maintain a small component/state specification and adaptive appearance | Product opportunity | M |

### UX-01: History discoverability and input equivalence

**Evidence:** `app/static/js/history.js:205-261` recognises wheel, touch and selected
key gestures before revealing rows. `app/templates/history.html:63` tells keyboard
users to use Page Down or End. The scroll link is available in the initial waiting
state; it is hidden after loading (`history.js:196`). Rows that have not been
revealed are not available for normal reading or Tab navigation. Source inspection
does not establish what happens when a screen reader consumes those keys, uses
browse-mode navigation, moves its virtual cursor or sends a scroll command.

**Recommendation and benefit:** evaluate the requested interaction first with
NVDA/Firefox or Chromium and VoiceOver/Safari, plus keyboard-only, touch and voice
or switch input. Check that each user can discover and reach successive reports,
understand the count and reach pagination. If a supported combination cannot
continue, propose a normal named activation or alternate input path that preserves
one-row reveal and the empty start. Do not silently override the user's design.
The tradeoff is accommodating conventional navigation while keeping gesture
locking and preventing momentum from revealing several reports.

**Acceptance:** zero initial report-list requests and rows; an intentional reveal
exposes one row; no synthetic layout/restore scroll starts loading; every supported
input can reach all 24 rows and the next page without special timing; revealed
content does not steal focus; no AT user must turn off their reader to continue.
Announce a useful count once per meaningful change and verify actual speech.
These are proposed product checks, not proof of the whole site's conformance.
[WCAG keyboard guidance](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html),
[status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
and [GOV.UK pagination guidance](https://design-system.service.gov.uk/components/pagination/)
support the evaluation. GOV.UK advises against infinite scrolling because of
keyboard problems; its guidance does not approve this custom within-page reveal.

### UX-02: Stable running-job actions

**Evidence:** `app/static/js/setup-tools.mjs:92-95` replaces the entire overview when
the JSON snapshot changes, then creates new Open/Cancel controls. The next poll
runs after four seconds. The unchanged-snapshot guard helps, but an actual progress
update can remove a focused action node. Lost focus is a source-supported risk,
not an observed browser failure in this review.

**Recommendation and benefit:** keep job rows keyed by scan ID and update status
text in place; preserve their action controls. If a job disappears, choose an
explicit useful focus destination only when that row contained focus. This lets
someone inspect or cancel a job at their own pace. The tradeoff is slightly more
state reconciliation code.

**Acceptance:** focus Open progress, Open saved report and Cancel in turn; return
changed progress on several polls; the same focused action remains usable. Test
job completion, disappearance, two jobs, cancellation pending and request failure.
Announce meaningful changes without reading every poll or moving focus.
[WCAG focus-order guidance](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html)
and [status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).

### UX-03: Distinct identities in destructive controls

**Evidence:** `history.js:53` and `:81` use only `reportName(report)` for Select/Delete
accessible names. `openDelete()` at `:270` lists only that name in confirmation.
Default names such as "Light report" or user-entered titles can repeat. Dates and
scan type appear in the ordinary row but not the confirmation list.

**Recommendation and benefit:** include title, scan type and recorded date in each
confirmation item and control name; include the recorded target if available and
needed to distinguish same-time reports. Keep any technical identifier in optional
details. Users can verify the intended record before deletion. The tradeoff is
longer labels; keep visual hierarchy and accessible descriptions readable.

**Acceptance:** two default titles and two identical custom titles remain
distinguishable in screen-reader control navigation and the dialog. Long titles
wrap. Confirmed selection matches exactly the shown eligible reports; Cancel and
Escape retain the safe default and meaningful focus return. Keep the current
revision checks and partial outcomes. [W3C modal-dialog guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
and [error prevention for user data](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html).

### UX-04: Date and timezone clarity

**Evidence:** `app/static/js/presentation.mjs:18` uses `date.toLocaleString()` after
validating timestamp timezone information. History From/To labels explicitly use
UTC (`history.html:28-32`). The row date is browser-local and lacks a zone label,
so a report around midnight can display a different calendar day from its UTC
filter day. This is an implementation mismatch, not a claim that stored timestamps
are incorrect.

**Later live-data corroboration by the main agent:** the completed pair in
[the 14 October live record](live-check-20261014.md) displayed 14 October locally
while both creation timestamps were on 13 October UTC. The isolated search returned
two reports for 13 October UTC and none for 14 October UTC. The review agent did
not run that check; the original timestamp values were preserved.

**Recommendation and benefit:** explicitly label the display zone and describe
date-filter boundaries beside the date inputs. Choose either clear UTC filters
with local display or local-day filters converted at the API boundary; retaining
saved UTC evidence is compatible with either. Label relative times with an exact
date available. The tradeoff is consistency versus locally familiar dates; make
one explicit product choice rather than using the execution host's timezone.

**Acceptance:** reports on each side of UTC midnight, browser zones ahead/behind
UTC, Europe/London DST transitions, inclusive end dates and uncertain legacy
timestamps. A user can explain which day a displayed report matches. Preserve
the current invalid-timestamp fallback and do not infer missing timezone data.
This is a consistency recommendation under
[Nielsen's heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/),
not a specific WCAG date-format mandate.

### UX-05: Durable settings feedback and dirty state

**Evidence:** `app/static/js/settings.js:154` says changes apply only on Save; browser
preferences actually apply immediately, as their separate section correctly
explains. At `:194-195`, success is written to a live region immediately before
navigation to Home, where no equivalent success notice is provided by this flow.
The settings controller has no dirty-state tracking or resumption for edited server
settings. Conflict handling already preserves input and warns before reload.

**Recommendation and benefit:** qualify the server-form message as "Network and
scanner settings apply when saved". Either stay on Settings with a durable Saved
state or show an equally durable, accessible confirmation on the destination.
Show a concise unsaved state only after a real change; make discard/resume clear
without warnings on unchanged navigation. Preferences need their own brief
"Applied in this browser" feedback and truthful storage-unavailable status.
The tradeoff is more navigation state and the annoyance of overused leave prompts.

**Acceptance:** a slow screen reader can perceive save success; changing display
preferences does not dirty the scanner form; failed/conflicting saves retain input;
returning or discarding works intentionally; blocked browser storage is clear.
Use targeted inline messages and linked summaries for validation.
[GOV.UK error-summary guidance](https://design-system.service.gov.uk/components/error-summary/)
and [Carbon notification guidance](https://www.carbondesignsystem.com/building-blocks/core/components/notification/guidelines).

### UX-06: Recovery and disk-space management

**Evidence:** the report-management record documents recovery receipts held only
in the open page and a private archive excluded from existing saved-size/export
measurement. `history.js:17` holds Undo receipts in memory. The template truthfully
explains these limits, but readers must use operator instructions to recover after
navigation and cannot inspect recovery size from the current measurement.

**Recommendation and benefit:** design a bounded authenticated recovery browser
with titles, dates, removal time, size and Restore. Report active-data and recovery
sizes separately, and make export coverage explicit. Surface the archive capacity
when it prevents further removals. This supports ordinary recovery without needing
to remember a receipt or find a filesystem command. It needs backend work, safe
receipt discovery, pagination and the same admission/path/revision protections.
No automatic purge, retention period or permanent-delete action is authorised by
this recommendations document; those are separate product decisions.

**Acceptance:** delete synthetic finished reports, navigate away/reload and recover
them through the planned UI; distinguish same-title entries; preserve names and
settings; refuse overwrite; report mixed outcomes and full/unsafe archives; show
accurate active/recovery totals; reconcile after an uncertain response without
automatically repeating a destructive request.
[Error prevention for user data](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html)
supports recovery as a design rationale, not a requirement for this exact browser.

### UX-07: Accessibility beyond automated desktop checks

**Evidence:** report section navigation is conditionally sticky
(`app/static/css/app.css:424-431`), and the History stage intentionally starts at a
viewport-height minimum (`:521`). Controls use custom theme colours and layouts.
The project records leave physical-device and assistive-technology evaluation open;
the latest report-management record also leaves current WebKit verification open.

**Recommendation and benefit:** evaluate the full journeys at 200% and 400% zoom,
320 CSS pixels, increased text spacing, browser high-contrast/forced colours,
landscape and large text. Measure actual hit areas, not just icon sizes. Existing
44-pixel targets are a useful product target; WCAG 2.2 AA SC 2.5.8 generally uses
24 by 24 CSS pixels with exceptions/spacing alternatives. Do not report 44 pixels
as the AA minimum. Device reduced motion should continue to override app motion.

**Acceptance:** no hidden actions, lost prose or two-direction page scrolling for
ordinary content; technical tables may have appropriate local scrolling; keyboard
focus remains visible and is not entirely obscured by authored sticky content;
selected/error/priority states survive loss of colour; dialogs remain operable;
text-spacing overrides do not clip labels. Check reduced motion separately from
contrast and focus. [Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html),
[text spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html),
[focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html),
[target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
and [use of colour](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).
[Animation from interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html)
is Level AAA; respecting it is valuable but must not be mislabelled an AA criterion.

### UX-08: Wording provenance where a result is read

**Evidence:** `showDetail()` in `app/static/js/scan.js:472` shows uncertainty and
evidence-strength text. Its AI-versus-reviewed wording source is inside Sources
and technical details; the report-wide model/source is also in a disclosure.
CVE research already qualifies matches and explains the optional lookup.

**Recommendation and benefit:** show one short source label near the item heading
or explanatory text, such as "Reviewed guidance" or "Local AI assisted wording",
with a named path to the existing source details. Retain factual caveats in the
main content, and explain that wording acceptance checks are not independent
verification of device safety. This improves calibrated trust with little added
visual weight. Avoid badges on every sentence or introducing new AI actions.

**Acceptance:** mixed accepted/fallback wording, failed/retried AI and old saved
records show their real source; unavailable metadata stays unknown; the label
works without colour or hover; participants can distinguish a saved observation,
wording assistance and their own Checked annotation.
[Carbon for AI](https://www.carbondesignsystem.com/building-blocks/foundations/carbon-for-ai)
and [Microsoft HAX](https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/)
motivate transparent capabilities, limits and contextual explanation.

### UX-09: Returning to the right History context

**Evidence:** History ends with `feed.reset()` and does not persist its submitted
filters or current page. Report reading state already uses per-report session
storage (`scan.js:80-158`). Search and page navigation can therefore be reworked
after opening a report and returning, depending on browser page-cache behaviour.

**Recommendation and benefit:** retain the submitted search/filter/page context
per tab and visibly indicate applied filters. Preserve the required empty initial
render when rebuilding the page; let deliberate reveal resume the chosen bounded
page. Clear destructive selection. Offer Clear filters prominently when no results
match. This reduces repeated work without automatically loading hidden reports.
Use bounded private session state rather than putting device names/addresses in
URLs by default; the tradeoff is reduced shareability and explicit invalidation
when the library changes.

**Acceptance:** open/return, reload without browser page cache, expired state,
blocked storage, missing last page and changed matches. No stale selection survives;
filters still apply across the whole library; no initial request/reveal; a report
opened in another tab does not overwrite the first tab's context.
[Recognition rather than recall](https://www.nngroup.com/articles/recognition-and-recall/)
provides the usability rationale; no specific storage method is required.

### UX-10: Task resumption and contextual help

**Evidence:** `app/templates/scan.html:151-165` already distinguishes To check,
Checked and Need help; status is explicitly a user's review, not a verified fix.
Home explains both scan types and the picker shows date/source context.

**Recommendation and benefit:** test a novice's end-to-end understanding before
adding more onboarding. If evidence shows a need, add a compact resume cue to the
first unfinished or Need help task, and a relevant local help link where a device
cannot be recognised. Keep manual review flexible and precautions visible before
the risky action. Do not make "all tasks Checked" a security score or force users
to complete them to read a report. The tradeoff is a shorter route to useful work
versus another status/control competing with the existing first action.

**Acceptance:** the reader can choose Light versus Deep, identify the selected
target, explain an unanswered check, resume an independent action and ask for help
without marking it Checked. Saved marks remain per action and survive reload.
[GOV.UK task guidance](https://design-system.service.gov.uk/patterns/complete-multiple-tasks/)
supports flexible completion; [GOV.UK details guidance](https://design-system.service.gov.uk/components/details/)
warns against hiding information most users need.

### UX-11: Consistency and adaptive preferences

**Evidence:** `app/static/css/app.css` already has theme/spacing tokens, but Home
and report use standalone templates while History/Settings extend `base.html`.
`appearance.js:5-7` currently supports Dark and Light, not a system-theme choice.

**Recommendation and benefit:** maintain a small internal state/component reference
for buttons, inline errors, summaries, dialogs, loading/empty/unavailable states,
navigation and provenance labels. Verify shared components in both themes and
forced colours. A later optional "Use device theme" choice can follow system
colour preference while explicit Light/Dark still wins. Do not introduce a large
UI framework solely for consistency. Costs include migrating component ownership,
preference compatibility and ensuring first paint uses the right theme.

**Acceptance:** each page exposes the same named/focused shared navigation and
comparable state messages; system-theme changes update only when opted in;
explicit choices persist; blocked storage has a usable fallback; movement still
respects device reduced motion. Adopt the consistency principle, not another
design system's whole visual language.
[Nielsen's consistency heuristic](https://www.nngroup.com/articles/ten-usability-heuristics/)
and the [NHS design-system approach](https://service-manual.nhs.uk/design-system).

## What to measure before expanding features

Use a small formative study with representative novice network owners and people
using assistive technology. Choose sample size, consent and private-data handling
with the project's study protocol; no participant work was conducted here. Use
fictional/prepared evidence wherever live traffic is unnecessary.

Adapt HEART's goal-to-metric process to four concrete goals: understand the scope
before starting, find the intended saved report, interpret uncertainty safely,
and recover an accidental removal. Record completion, wrong-target/wrong-report
choices, assistance needed, recovery success and whether the reader distinguishes
Checked from verified fixed. Time is useful alongside success and comprehension,
not a target to minimise at the expense of careful review. A few formative sessions
can identify problems; they cannot estimate population success or certify access.
[HEART primary research](https://research.google/pubs/measuring-the-user-experience-on-a-large-scale-user-centered-metrics-for-web-applications/).

Suggested study tasks: choose the appropriate scan, understand a long Deep check,
recognise an unnamed device, read one review item, mark Need help, retrieve a
same-title report by date, select only shown reports, cancel deletion and recover
after leaving the page. Record what the participant says happened, rather than
only whether they clicked the intended control. Avoid publishing raw device names,
addresses, screenshots or notes as study evidence without appropriate handling.

Defer decorative motion, dashboard security scores, unsolicited notifications,
command palettes, AI chat and forced onboarding until a task study shows a need.
The useful current patterns for this app are dependable state feedback, reversible
actions, contextual explanation, resumption and accessible preferences. This is
a product recommendation, not a claim that those other features are inherently
unusable.

## Remaining verification limits

This review did not run accessibility tools, verify calculated contrast/hit areas,
listen to screen-reader announcements, test a physical phone or recruit readers.
It does not replace the separate live-scan record and supplies no new scan result.
Windows desktop tests do not establish mobile Safari behaviour; an old WebKit pass
does not resolve the current startup/verification limitation. The reviewed
report-management record lists skipped Windows link-creation tests and remaining
platform/participant/AT checks; retain those distinctions.

Treat WCAG 2.2 A/AA as an explicit proposed evaluation target if the project adopts
it; do not claim legal applicability or full conformance from these selected checks.
WCAG Understanding pages and APG patterns are explanatory guidance; the normative
standard is [WCAG 2.2](https://www.w3.org/TR/WCAG22/). WAI itself describes its
[Easy Checks](https://www.w3.org/WAI/test-evaluate/preliminary/) as preliminary,
not comprehensive or definitive. References were browsed on 14 October 2026.

The proposed implementation order is UX-02/03/04/05, concurrent UX-01/07 evaluation,
then a concrete recovery/storage design for UX-06. Reprioritise UX-08/09/10/11 using
observed task failures and the new live-scan findings. No application change,
report deletion, retention policy or external action is implied by this document.
