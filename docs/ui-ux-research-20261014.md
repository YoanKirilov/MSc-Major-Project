# Inclusive UI/UX research and next steps — 14 October 2026

Implementation follow-up, 15 October: see [changes and verification](inclusive-ui-implementation-20261015.md).
The research below records the original findings; code changes and prepared inclusive
evaluation tasks are tracked separately. Actual participant/assistive-technology
sessions remain unperformed and no accessibility certification is claimed.

Status: research and source inspection, not another redesign or an accessibility
certification. The requested spacing and smaller device-footer controls are being
handled separately by the main implementation agent. This review changes only this
document; it starts no scans and collects no participant data.

The best next improvement is clearer content and a more predictable journey, not
more controls. Preserve the home page, native Supporting information dialog,
24-record pages, reversible deletion and the distinction between observations and
security conclusions. Technical experience and disability are independent: a
disabled person may be an expert, and a nondisabled person may need extensive help.

## Scope and interpretation

Reviewed the current Home, My devices, Saved reports, Settings and report templates;
appearance, inventory, report-navigation and notes controllers; shared CSS; and the
existing quality/evaluation plans. Function names and selectors below are more
durable than line numbers while implementation continues.

This is a bounded survey of current primary guidance and established research.
It cannot cover every practice or prove which appearance is most popular. Current
publication does not make an interface suitable for this app. Conversely, useful
established research does not become obsolete merely because it is older.

Use WCAG 2.2 AA as an evaluation target. The normative standard covers full pages
and complete processes; passing selected automated checks or importing an accessible
component does not establish app-wide conformance. W3C Understanding pages explain
the criteria rather than adding extra normative requirements. GOV.UK and USWDS
component conventions are design guidance, not rules NetGuard must copy verbatim.
[WCAG 2.2 and conformance requirements](https://www.w3.org/TR/WCAG22/#conformance).

Current, useful patterns include task-oriented content, progressive disclosure,
native semantic controls, durable feedback, reversible actions and adaptive layout.
These are established patterns, not a reason to introduce a new framework,
gesture-driven feed, animation-heavy dashboard or AI chat interface.
[Progressive disclosure research](https://www.nngroup.com/articles/progressive-disclosure/).

## What already works and must stay

- Home explains Light versus Deep by purpose, requires a deliberate Scan action,
  shows saved progress below setup and labels stage progress as not time remaining.
- Reports show a first action, plain-language headings, unknown coverage, explicit
  AI/editorial provenance and technical evidence on request. Checked is not treated
  as a verified fix; unnamed devices are not labelled intruders.
- Supporting information now uses one native dialog with labelled topics, visible
  Close, Escape, focus return and separate content scrolling. Keep this interaction.
- Search inputs have visible labels; technical tables have their own scroll region.
  Whole-page horizontal scrolling is not the intended ordinary-reading interaction.
- My devices distinguishes saved observations and household labels from live status
  and verified identity. Search/view applies across the included inventory.
- Saved reports provides bounded pagination, distinct deletion confirmation, Undo
  and a persistent recovery list. Do not reintroduce scroll gestures as a prerequisite
  for accessing records.
- Settings separates immediately applied browser preferences from server settings
  requiring Save. Reduced motion follows the device without another app selector.

These are source observations. This research task did not rerun the browser matrix,
measure actual spoken announcements or assess real readers' understanding.

## Prioritised recommendations

P1 means the next small implementation/evaluation batch, not a proven critical
defect. P2 follows once primary tasks have been evaluated. Effort is relative scope,
not a delivery estimate.

| ID | Priority | Next step | Evidence | Effort |
| --- | --- | --- | --- | --- |
| IUX-01 | P1 | Refine existing plain-language layers; retain essential cautions | Source-supported opportunity; comprehension unmeasured | M |
| IUX-02 | P1 | Put household recognition and review needs ahead of technical history | Source-supported opportunity | S–M |
| IUX-03 | P1 | Carry the selected device into its saved report | Source navigation observation | M |
| IUX-04 | P1 | Make display preferences consistent on every page | Concrete source inconsistency | S |
| IUX-05 | P1 | Evaluate concise, nonduplicated save/error announcements | Source-supported evaluation risk | S–M |
| IUX-06 | P1 evaluation | Finish keyboard, screen-reader, zoom and physical-mobile checks | Unverified combinations, not a claimed failure | M |
| IUX-07 | P1 evaluation | Run inclusive task and comprehension sessions | Existing prepared protocol; results outstanding | M |

### IUX-01 — improve the wording that already exists

`scan.js/showDetail()` already provides What we found, What this means for you,
What we could not confirm and What to do next. Keep that structure. Review the
paragraphs within it and the long inventory/comparison hints: phrases such as
bounded inventory, included observations, answering features and reliably matched
observations still require interpretation.

Prefer short literal sentences and one instruction per step. Explain a necessary
technical word beside its first use; leave exact ports, raw replies and model
diagnostics in existing supporting content. State the important limitation once
where it affects a decision, instead of repeating the same general disclaimer in
every paragraph. Never hide unfinished checks, identification uncertainty or
precautions before opening an HTTP page. Plain language is not removal of evidence.
[GOV.UK interface writing](https://www.gov.uk/service-manual/design/writing-for-user-interfaces),
[W3C cognitive accessibility guidance](https://www.w3.org/TR/coga-usable/#use-clear-and-understandable-content).

Illustrative editorial alternatives, to check against each report's facts:

- Bounded inventory: “This list uses the saved reports included here.”
- Not observed open: “This feature did not answer these checks this time.”
- No reliable comparison: “We could not match this device to an earlier completed
  check, so we cannot say what changed.”

Benefit: reduces reading and memory demands for novices, people with cognitive or
learning disabilities and people reading in a less familiar language. Tradeoff:
brief wording can omit important conditions; keep the conditions visible when they
affect the proposed action. Do not let Ollama replace factual severity or coverage.

Acceptance: compare old/new text against identical synthetic facts; preserve every
essential limitation and next-action precaution. Ask readers to explain what was
found, what remains unknown and what they would do first, without coaching. A
readability score or accepted model output is not a comprehension result.

### IUX-02 — make the inventory easier to scan, not merely denser

`device-library.js/deviceRow()` currently presents seven fact rows before the saved
reports and household-label disclosures. Keep the useful saved status, but evaluate
a compact primary group: device name, last recorded check, review-item count and
unfinished-check count. Move recorded network, first observation and detailed
report totals into a clearly labelled existing history/details area. Exact dates
remain available; a relative date must not replace them or imply a device is online.

Keep one primary save action in the label editor. Consider shorter visible wording,
such as “Save my labels”, with a nearby explanation of what is saved. Do not make
Save, Discard and conflict recovery equally prominent or icon-only. A shorter label
must still say what will happen. The main agent's requested spacing/footer sizing
work is already in progress; this review does not classify that work as missing.
[USWDS button guidance](https://designsystem.digital.gov/components/button/),
[GOV.UK details guidance](https://design-system.service.gov.uk/components/details/).

Benefit: quicker recognition for home users and less visual scanning for people
using magnification. Tradeoff: secondary history takes another disclosure action;
keep review needs and unresolved checks visible. Acceptance: readers can find an
unnamed device, identify its last recorded check and save a room label without
opening technical history. Confirm all original facts remain reachable.

### IUX-03 — open the device, not a general device section

Inventory report links currently append only `#devices-title` when a saved
`report.device_id` is available. A person choosing a particular device can arrive
at a report containing several devices and have to find it again. This is a source
navigation observation, not a reproduced failure in this research task.

Carry the saved device ID as bounded reading context and reveal that device's card
or review items when the report contains it. The context must never change scope,
authorise a scan or start one. If the ID is absent, explain that the requested device
cannot be highlighted and retain the complete report. Keep normal browser Back and
the existing per-page search/context restoration.

Benefit: reduces memory, address transcription and repeated navigation for novices,
keyboard users and users with cognitive impairments. Tradeoff: links need stale-ID
fallbacks and reading-state precedence rules; never silently choose another device.
Acceptance: open each device from a multi-device synthetic report, use Back, reload,
repeat after a saved device is missing, and confirm no new scan/provider request.
This is an application of predictable task navigation, not a WCAG requirement for
a particular URL format. [USWDS design principles](https://designsystem.digital.gov/design-principles/).

### IUX-04 — use the same preference choices everywhere

Concrete source inconsistency: Settings has Dark, Light and Use device theme;
the report dialog currently has only Dark and Light. `appearance.js/render()` sets
each native select to the saved `preferences.theme`. A saved system choice can
therefore have no matching selected report option, even though its effective colour
theme is correctly applied. This is inferred from code; no live/browser reproduction
was performed by this research task.

Share the choices/labels between the two native controls, including the system
choice, without adding a new preference. Keep text-size choices and automatic OS
reduced motion. Make the existing applied/remembered feedback available in both
locations; blocked storage must not claim persistence.

Benefit: predictable controls for every reader, including people adapting colour
or text for low vision. Tradeoff: one more existing choice in the report select,
but no second competing state. Acceptance: choose system in Settings, open a report,
change the OS theme, return to Settings, block browser storage and check cross-tab
updates. Both selectors must show a valid choice and the actual preference.
[WCAG consistent identification](https://www.w3.org/TR/WCAG22/#consistent-identification).

### IUX-05 — make recovery understandable without repeated announcements

Keep durable save confirmation and drafts on failure. Settings already has an
error summary; inventory editors show inline status. `scan.js/actionChecklist()`
updates a page-level status and row-level status with the same save message.
Multiple live regions may repeat speech, but this requires actual assistive-
technology evaluation before calling it a defect.

Define one concise announcement per meaningful operation and keep useful visible
feedback next to the affected control. State separately: saved, not saved, or save
not confirmed. For uncertain writes, retain the draft and offer a named reload/check
action; do not automatically repeat an edit or destructive action. Errors should
identify the field and a useful next step rather than expose implementation terms.
[WCAG status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html),
[GOV.UK error summaries](https://design-system.service.gov.uk/components/error-summary/),
[GOV.UK notification guidance](https://design-system.service.gov.uk/components/notification-banner/).

Benefit: less uncertainty for all users and less interruption for screen-reader
and cognitive-accessibility users. Tradeoff: reducing speech must not make outcomes
silent. Acceptance: delayed/conflicting saves, lost responses, failed reloads and
Delete/Undo/Restore; the original input survives and each outcome is spoken once
usefully. Test visible error-to-field association and focus, not just `role` markup.

### IUX-06 — preserve the dialog and finish inclusive interaction evaluation

The dialog is a useful secondary reading surface. Do not revert it to rearranging
below-fold panels. Check its heading, topic selector, independently scrollable
content, Close, native Escape and return to the actual invoker with real readers.
Structured dialog content should not be announced as one enormous description.
[WAI modal-dialog guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).

Evaluate the whole task journey, not only the dialog: skip link, navigation,
search, device labels, review-item selection, tasks, Settings, deletion and recovery.
Native semantics and visible labels remain the default. Make spoken command names
contain the visible label; do not shorten visual buttons by replacing their names
with unrelated hidden wording. [Keyboard guidance](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html),
[label-in-name guidance](https://www.w3.org/WAI/WCAG22/Understanding/label-in-name.html).

Keep ordinary prose/actions usable at 320 CSS pixels, 200% text/zoom and 400% browser
zoom, including short landscape screens and an open mobile keyboard. The technical
table may retain its separately identified horizontal scroll region. Allow user
text-spacing overrides without clipping; this does not require another settings
control. [Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html),
[text spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html).

Check normal text contrast at 4.5:1, qualifying large text at 3:1, and required
control/state cues at 3:1 against adjacent colours, with applicable exceptions.
Review light/dark/system/forced-colour states and focus, not screenshots alone.
[Text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html),
[non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).

For compact footer actions, distinguish visual size from hit area. WCAG 2.2 AA
SC 2.5.8 generally requires 24×24 CSS-pixel targets or a listed exception, including
sufficient spacing; it is not a universal 44-pixel rule. Retaining comfortable
44-pixel primary targets is a product choice. Smaller-looking controls must remain
easy to activate and not overlap. [Target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

Focus must be visible and not entirely obscured by author-created content for the
AA minimum. Prefer fully visible controls as a stronger product goal, especially
under the report's sticky navigation. [Focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html).
Dark mode, reduced motion and headless reflow passes alone do not certify access.

### IUX-07 — test safe understanding with disabled and nondisabled readers

Extend `docs/evaluation-session.md`, rather than create another competing study.
Include nontechnical users, people using screen readers/magnification/keyboard or
voice input, people with cognitive or learning accessibility needs and older users
where relevant. Let participants use their familiar assistive technology. Do not
treat one participant as representative of a whole disability group.
[WAI involving-users guidance](https://www.w3.org/WAI/test-evaluate/involving-users/).

Use synthetic facts and university-approved consent/ethics arrangements. Ask people
to find the first useful action, distinguish unfinished from safe, label a device,
reopen its report, change text/theme and recover an accidentally deleted report.
Do not collect home-network identifiers or ask them to change real device settings.

Record task completion, help needed, mistakes, confusing words and unsafe
interpretations separately from clarity ratings and time. Include the combined
interface's actual AI/editorial/fallback wording. An AI-only comparison needs fixed
controlled conditions; the normal UI must not be relabelled as that experiment.
Keep factual limitations and wording provenance inspectable.
[Microsoft human-AI interaction guidelines](https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/).

Benefit: reveals barriers that automated tools and an imagined novice cannot
confirm. Tradeoff: recruitment and accommodations take work, and a small study is
exploratory rather than statistical proof. Acceptance: prospectively agreed tasks
and scoring, anonymous findings, all unsafe conclusions recorded, an independent
review of scoring, and a follow-up round after targeted fixes.

## Executable order for a later batch

1. Record the current interface/version and preserve saved evidence. Reuse the
   existing quality/evaluation acceptance targets rather than inventing new pass
   thresholds after seeing results.
2. Fix the concrete preference-choice mismatch and add Settings→report/system-theme
   regressions. Keep the dialog and home layout unchanged.
3. Make a small editorial prototype for representative completed, unfinished,
   unnamed, zero-item and AI-unavailable synthetic reports. Review safety/evidence
   fidelity before presenting it to readers.
4. Prototype inventory hierarchy and exact-device report context. Test stale links,
   browser Back/refresh, long labels and no unexpected scan/provider traffic.
5. Evaluate live-region output and error recovery with actual assistive technology.
   Change only announcements shown to be redundant or unclear.
6. Run automated semantics/layout checks and keyboard review, then physical-device,
   assistive-technology and inclusive-reader sessions. Record browser/OS/AT versions
   and untested combinations. An automated scanner cannot evaluate comprehension.
7. Implement the smallest changes supported by the observations, retest affected
   flows and update traceability. Do not claim every user can use the app or that
   WCAG conformance has been established without the required full assessment.

Avoid adding floating accessibility toolbars, custom read-aloud, dense risk charts,
auto-moving cards, compulsory wizards or extra filters merely because another
product uses them. Support normal browser/OS/assistive-technology features first;
evaluate additional aids only against a demonstrated user need.

All cited external guidance was checked on 14 October 2026. Standards, design-system
guidance and source-based product inferences are deliberately separated. This task
ran no tests, scans, screen-reader sessions or human study; only the new research
document was written.
