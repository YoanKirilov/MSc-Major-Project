# UI/UX review and implementation brief — 8 October 2026

## Outcome and scope

The display problems are real. The most serious reproduced faults are a checklist placed in the wrong CSS grid column, keyboard focus lost when a result is selected, and mobile explanations appearing far below their triggering result. There are also inconsistent device-card boundaries, overflowing search controls, and an overloaded information hierarchy.

This is a research-first review, not a completed redesign. Production templates, JavaScript, CSS, scan evidence, settings and nicknames were not changed in this review. Temporary CSS proposals were applied only inside the audit browser to check that the layout fixes are feasible. No Nmap scans, identification lookups, Ollama requests, CVE queries or Pi-hole requests were run.

The recommendation is to preserve the dark/teal identity and the existing factual scan architecture, while rebuilding the presentation around predictable components and clear user tasks. Neither changing FastAPI nor introducing a database is needed to solve these UI problems.

### Evidence and limitations

- Source inspection: dashboard, report, Settings and Saved reports templates; their JavaScript; shared stylesheet; responsive browser tests.
- Current Chromium rendering of isolated copies of the latest saved Light and Deep reports. These include many devices, long names, unnamed devices, an unfinished host, multiple service types and self-scan notices.
- Six page/state types at 320 × 568, 390 × 844, 768 × 1024 and 1440 × 1000: Light setup, Deep setup, Light report, Deep report, Settings and Saved reports. Also inspected the Deep run-again dialog, expanded checklists, result selection, simulated 200% root text size and two temporary layout prototypes.
- 27 measurement sets: 24 normal page/viewport combinations, one text-size simulation, two prototypes. No browser JavaScript exceptions or report mutation requests; no external browser requests. The audit used an ephemeral loopback server and its own JSON folder, then stopped that server.
- Private screenshots, harness and measurements are in `.test-artifacts/ui-ux-review-20261008/`. They contain private network details and should not be published unredacted.
- No new Firefox/WebKit, physical-device, screen-reader or nontechnical-reader study was performed for this review. No automated accessibility conformance certification is claimed. Simulated text enlargement is not a complete browser-zoom test. An absence of horizontal page overflow does not establish that controls inside the page are correctly arranged.

Finding labels below distinguish **reproduced** layout/interaction faults, **source-confirmed** implementation behaviour and **recommendations** requiring user testing. P1 means fix first because a task or essential information is affected; P2 means substantial usability improvement; P3 means consistency/maintainability improvement. These are UI priorities, not vulnerability severities.

## Research translated into requirements

There is no universal correct arrangement for every dashboard. Use measurable accessibility requirements, established component patterns, and task testing with the intended audience together.

1. **Consistent anatomy, not arbitrary fixed heights.** Cards can legitimately have different heights. The issue here is that matching information and actions change position, making devices difficult to compare. Predictable rows or summaries are better for comparing similarly structured devices. Do not crop useful content to make every box identical. [NN/g: Cards](https://www.nngroup.com/articles/cards-component/), [NN/g: Data tables and user tasks](https://www.nngroup.com/articles/data-tables/).
2. **Label facts explicitly.** Use key/value summaries for a device's address, reported name, source and check status; use lists for services/tasks and tables for technical comparisons. Do not treat every kind of data as a paragraph or card. [GOV.UK: Summary list](https://design-system.service.gov.uk/components/summary-list/).
3. **Give actions a clear hierarchy.** Primary styling should identify the main action, not every nickname edit. Distinguish navigation, secondary actions and destructive actions. [GOV.UK: Button](https://design-system.service.gov.uk/components/button/).
4. **Use a spacing scale.** Define consistent gaps within controls, between related controls and between sections, with responsive adjustments. The exact scale proposed below is this app's design choice, not a WCAG requirement. [GOV.UK: Spacing](https://design-system.service.gov.uk/styles/spacing/).
5. **Keep essentials visible; disclose supporting detail.** Show device identity, completion, review priority and the next action immediately. Expand evidence, original wording and advanced references on request. Do not hide information most users need. [GOV.UK: Details](https://design-system.service.gov.uk/components/details/).
6. **Do not solve everything with tabs.** They can hide important information and make comparison harder. Start with headings, clear summaries and contextual expansion; evaluate tabs only where the tasks support them. [GOV.UK: Tabs](https://design-system.service.gov.uk/components/tabs/).
7. **Design accessible interactions.** Target WCAG 2.2 AA. Its minimum target criterion is 24 × 24 CSS pixels, with specified exceptions including sufficient spacing; 44 × 44 is the enhanced AAA target and a useful app touch-design goal. Small targets are not automatically violations. [W3C: Target size minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html), [W3C: Target size enhanced](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html).
8. **Support reflow, contrast and keyboard use.** Ordinary content should reflow at 320 CSS pixels without losing functionality. A genuinely two-dimensional technical table may have its own horizontal scrolling. Normal text generally needs 4.5:1 contrast, large text 3:1, subject to criterion exceptions. Focus order must remain meaningful. [W3C: Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), [W3C: Contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [W3C: Focus order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html).
9. **Use familiar words without misleading simplification.** Explain uncommon terms at their point of use. Avoid replacing technical terms with unfamiliar euphemisms. Plain language must preserve uncertainty and limits. [W3C cognitive guidance: Clear words](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o3p01-clear-words/). This is supplemental guidance, not an additional mandatory AA criterion.

## Findings, in execution order

### UI-01 — Checklist controls occupy the numbering column — P1, reproduced

**Evidence:** `.remediation-list li` defines `24px 1fr` columns. Its generated number takes the first cell and the instruction takes the second. The subsequent `.action-check` has no explicit column, so it starts the next row in the 24-pixel numbering column. Measured checklist containers were 24 pixels wide on all four normal report widths. Their labels and 100-pixel selects overflow internally; a 390-pixel Light example used about 339 pixels of height per narrow checklist. Whole-page overflow tests still passed.

**Fix:** Explicitly place the checklist in the content column. Give its label a block/grid layout with a separate, full-width status control. Use a short visible label such as “Your review status”; provide device/action context through associated labels or descriptions rather than repeating the whole instruction.

**Files:** `app/static/css/app.css:187`, `app/static/css/app.css:249`, `app/static/js/scan.js:94`.

**Acceptance:** At 320 pixels and enlarged text, checklist labels, selects and feedback remain inside the instruction column. No overlap with numbering or original-step disclosures. Test element containment, not just document width.

### UI-02 — Selecting a review item destroys keyboard focus — P1, reproduced

**Evidence:** `renderFindings()` replaces all finding buttons. Their activation handler calls it again and then calls `showDetail()` a second time. After focusing a card and pressing Enter, `document.activeElement` became `BODY` at both 390 and 1440 pixels, for both reports.

**Fix:** Keep stable button nodes, update their selection state, and update the detail component once. Preserve focus on the trigger or deliberately move it to the revealed explanation according to a consistent interaction contract. Do not leave it on the body.

**Files:** `app/static/js/scan.js:471`, `app/static/js/scan.js:509`.

**Acceptance:** Keyboard activation has a visible, predictable focus destination. The next Tab reaches the expected next control. Selection, nickname updates and polling do not restart keyboard navigation.

### UI-03 — Mobile selection has no nearby visible result — P1, reproduced

**Evidence:** Below 880 pixels, the findings list and detail panel become one column, with the entire list before the panel. In the Light report, the selected detail started approximately 1,418 pixels below the viewport top after activating the first item at 390 pixels. There is no selected-item scroll/focus handling in that handler.

**Fix:** On mobile, show the explanation immediately after its selected row, or open a clearly labelled detail view with a return action that restores the row and scroll position. Keep the desktop master/detail approach only where both panes can usefully be read. Do not introduce a hidden independent scrolling pane as a quick fix.

**Acceptance:** A user tapping a result sees its heading and device context immediately. Returning does not lose filters or position. Essential actions remain reachable on short screens and by keyboard.

### UI-04 — Clear-search button is taller than its search box — P1, reproduced

**Evidence:** At 390 pixels, the search box measured 43 pixels high while its wrapping Clear search button measured 62 pixels. Its text visibly extended outside the boundary. Fixed box height, a 100%-width input and an unreserved trailing button compete for space.

**Fix:** Use a flexible input and a non-shrinking trailing control, a minimum rather than fixed height, and a consistent target area. Allow the button to move to its own row at genuinely narrow widths if necessary. Hide/disable clearing appropriately when the search is empty, with a predictable layout.

**Files:** `app/static/css/app.css:134`, `app/templates/scan.html:100`.

**Acceptance:** Search icon, input and Clear search remain contained at all viewports and text-spacing settings. Clearing preserves focus and makes filter scope clear.

### UI-05 — Priority badge breaks a word across lines — P1, reproduced

**Evidence:** The Medium badge rendered as “MEDIU” / “M” at 390 pixels beside a long device name. The flex row allows the badge to shrink and inherited `overflow-wrap: anywhere` permits character-level breaks.

**Fix:** Give the badge a non-shrinking/max-content cell and allow the device context to wrap in its own cell or row. Keep the priority word intact without clipping other information.

**Files:** `app/static/css/app.css:167`, `app/static/css/app.css:302`.

**Acceptance:** All priority labels remain readable with long names at 320 pixels and enlarged text. Colour is not the only indication of priority.

### UI-06 — Some disclosure targets are undersized and crowded — P1, reproduced risk

**Evidence:** Technical scan details measured 17 pixels high; several disclosures measured 21 pixels. “View comparison details” and “Seen earlier, not matched this time” were stacked directly adjacent at 390 pixels: their vertical centres were only 21 pixels apart. This fails the spacing geometry for 24-pixel circles, unless another applicable criterion exception applies. Native inputs and inline links need separate exception/context assessment; do not treat the audit's `smallTargets` count as a WCAG failure count.

**Fix:** Use comfortable padded disclosure rows and explicit separation. Aim for 44-pixel touch rows for important controls; formally assess each target against the minimum criterion and its exceptions. [W3C: Target size minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

**Acceptance:** Adjacent actionable targets satisfy the adopted size/spacing rule. Text zoom is not used as a substitute for meeting CSS-pixel target requirements.

### UI-07 — Device-card boundaries and action positions are inconsistent — P2, reproduced

**Evidence:** The nickname toolbar is a sibling outside the bordered `<details>` card. The first desktop row contained cards about 473 and 351 pixels high; their nickname toolbars began about 123 pixels apart vertically despite belonging to the same grid row. The row groups stretched equally, but the visible boundaries and actions did not. On mobile, a bright nickname button floats below each collapsed card.

**Fix:** Make one enclosing component own the header, summary, optional body and action area. Keep names, status, counts and actions in predictable places. Prefer compact consistent rows for many comparable devices. If cards remain, align their action footers within each natural grid row; do not impose fixed heights or clip expanded content.

**Files:** `app/static/js/scan.js:660`, `app/static/js/scan.js:688`, `app/static/css/app.css:247`.

**Acceptance:** Sparse, rich, unnamed and failed devices share one anatomy. Optional information changes the detail body, not the identity/action placement. Expanded content remains readable.

### UI-08 — Nickname actions have too much visual priority — P2, reproduced

Every usable device gets a filled primary nickname button. With many devices, these are more visually insistent than the review workflow. Naming is useful but is normally a secondary action. Keep it clearly associated with its device and use a quieter secondary treatment. Similarly, the Deep run-again dialog presents two filled primary choices. Consider a radio choice followed by one Continue button, or two clearly equivalent secondary choices; do not privilege a dangerous assumption about an old address. [GOV.UK: Button hierarchy](https://design-system.service.gov.uk/components/button/).

**Acceptance:** A novice can identify the next main action without mistaking nickname editing for a required security task. Equivalent rerun choices are understandable and no scan starts automatically.

### UI-09 — Device identity is incomplete in collapsed summaries — P2, source-confirmed

The collapsed device header shows the name, feature count and review count; the address is inside the expanded body. Several devices can be unnamed, have similar names or reuse a nickname. The device type and the source of the displayed name are not part of the main summary either.

**Fix:** Keep a stable secondary identity line visible, including address and whether a name is user-supplied/reported. Show a supported category only as known or possible, never infer it from a friendly-looking name. Use “Device not identified” rather than an alarming intruder implication.

**Acceptance:** Two unnamed or identically named devices can be distinguished without opening a technical table. Historical/conflicting names remain visibly qualified.

### UI-10 — Important recognition details are buried in the technical table — P2, source-confirmed

“About this name”, alternate names, manufacturer and additional reported model/device details are assembled in the table's name cell, not the main device summary. This puts useful beginner information behind an advanced presentation.

**Fix:** Add an “About this device” key/value section in the device's own detail view. Include source and uncertainty locally. Keep the technical table as another view of the same underlying facts, not the only route to them.

**Files:** `app/static/js/scan.js:817` onwards.

**Acceptance:** Users can learn why a name/model is shown without opening the seven-column technical table. Contradictory, historical and advertised claims never become verified identity.

### UI-11 — Features beyond the first five require technical reading — P2, source-confirmed

Device summaries show at most five human-readable feature labels. Additional features are redirected to the device table. The Deep report has 13 open services, so much of the data leaves the beginner-friendly path.

**Fix:** Use “Show all 13 features” within that device's detail view, with concise labels and contextual explanation for each. Keep protocol, port, raw scripts and software fingerprints in supporting detail. Maintain one factual service list so the counts cannot drift.

**Acceptance:** All recorded open services remain accessible in plain language. A service without a rule finding does not disappear, and an unidentified service is not described as a known application.

### UI-12 — Different valid counts appear to disagree — P2, reproduced design issue

The Light example reports 23 checked devices, 24 device-result entries including a failed target, and naming coverage for the 23 parsed devices. Those are different denominators, not evidence of corrupt data, but the UI makes users reconcile them. “Features”, “services”, “review items” and personal checklist actions add further counts with different meanings.

**Fix:** Present one coverage equation: discovered / checked / could not check. Label the naming denominator and distinguish a target without a parsed result. Explain service and review counts once, close to the relevant number. Keep personal review progress separate from scan completion.

**Acceptance:** Every count has a defined population, including filtered counts. Do not merge failed targets into successful-device or name totals.

### UI-13 — The overview uses excessive height and repeats metrics — P2, reproduced

The desktop status/count card stretches to match a long hero column; the Light screenshot shows a large mostly empty panel. Its count and coverage are repeated by metric cards, the lead and later guidance. On 390 pixels the hero alone measured about 1,295 pixels, before the beginner guide.

**Fix:** Use one compact summary with finish state, coverage and review priorities. Let the panel size to its content, not the adjacent long narrative. Keep a prominent route to the first useful task. Preserve the incomplete-device warning and self-scan limitation instead of replacing them with a reassuring score.

**Acceptance:** Users can locate coverage and the recommended next action without reading multiple copies. Long failure messages expand supporting notes rather than stretch a decorative overview box.

### UI-14 — The report's sequence delays the useful work — P2, reproduced design issue

The order is overview → beginner guide → previous-scan comparison → findings → devices → announcements → next steps. At 390 pixels the device section starts around 6,956 pixels down the Light report, and next steps around 12,773. Comparison occupies a prominent section even when the private fixture has no prior report to compare.

**Fix:** Start with a compact overview and the recommended first task. Follow with device summaries and review details; put comparison in a clearly optional supporting section when useful. Keep short section links. Test priority-first versus device-first navigation with home users before committing to a large restructuring.

**Acceptance:** Users can find a named device, its review item and its next action directly. No arbitrary maximum page-height threshold is imposed: length is a task-efficiency measure, not a WCAG failure by itself.

### UI-15 — Repeated caveats and AI process notes overwhelm the answer — P2, reproduced

The UI repeats that results are not a safety verdict, features may be in use or not, names do not verify identity, guidance is reviewed, and AI may retain original wording. These are important safeguards, but several are repeated in the summary, card, evidence, actions and checklist. A selected item can read like an explanation of the system rather than the user's device.

**Fix:** Keep one short report-level limit statement and item-specific limitations near each result. Use a small “About this explanation” disclosure for model/provenance/validation details and original wording. Keep AI unavailable/failed state visible with a retry route. Essential uncertainty must never be hidden simply to make the page shorter.

**Acceptance:** Each result first answers: what answered, what it means for this device, what to check next, and what remains unknown. All supporting evidence and original explanations remain accessible.

### UI-16 — Vocabulary, repeated titles and tiny context reduce comprehension — P2, reproduced

Finding context uses roughly 11.5-pixel names and 12-pixel service text; both frequently truncate. Several items share “Check what this connection is used for” or “Device web page found (HTTP)” titles. Important distinctions such as device and service/port are secondary. “Contact number”, “feature”, “connection”, “service” and “review” are not interchangeable concepts for a beginner.

**Fix:** Use a short, consistent vocabulary and a readable context line. Name the actual observed feature in the item title where supported. Explain “port” once as a numbered connection point; avoid making users learn a new euphemism. Do not fabricate a purpose for unidentified services. Treat 16-pixel body text and 14-pixel secondary text as proposed design defaults, not WCAG-mandated font sizes. [W3C: Clear words](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o3p01-clear-words/).

**Acceptance:** Readers can distinguish two similar items without opening both. Essential identity/priority is not ellipsised with no alternative. Full context is available to keyboard, touch and assistive-technology users, not only mouse hover.

### UI-17 — Next steps do not expose the complete checklist — P2, source-confirmed

`renderNextSteps()` uses only the first action from each finding, groups these, and shows at most three groups. Meanwhile the global progress counts every finding action. In the Deep example, eight actions are counted, but the lower section does not expose all eight; the rest require selecting other review items above.

**Fix:** Make the lower section clearly “Suggested first steps” with a Show all review tasks route, or make it an authoritative complete checklist. Link each task to its device and evidence. Preserve saved action IDs and revisions; visual grouping must not merge distinct saved actions.

**Files:** `app/static/js/scan.js:515`, `app/static/js/scan.js:528`.

**Acceptance:** Every counted action has an obvious accessible route. Users can locate remaining tasks after marking the initially suggested ones reviewed. “Checked” never means a new scan passed.

### UI-18 — Checklist controls repeat long instructions in multiple places — P2, reproduced

The result detail and Next steps can show controls for the same action. Each label repeats the device name, address, feature and full action text. Next steps renders these inside a label with an inline select, giving the control a paragraph-like appearance.

**Fix:** Render one shared checklist component with concise labels, structured context and separate feedback. If the same action remains editable in two views, visibly identify the shared state and retain the existing revision/conflict protection. A multi-session task list is appropriate only if users actually need that workflow. [GOV.UK: Task list](https://design-system.service.gov.uk/components/task-list/).

**Acceptance:** A change updates all representations without moving focus or hiding the edited control. Full instructions appear once per displayed task; labels remain unambiguous.

### UI-19 — Search and filters have unclear scope — P2, source-confirmed

One search box lives in the findings section but filters both findings and devices lower down. Priority buttons affect findings only. Counts on priority chips are calculated from the full report, not recalculated for the search. The checklist filter only hides controls, not the associated instructions. These behaviours are not inherently wrong, but they create surprising combinations.

**Fix:** Explicitly scope search to the report or provide separately labelled device/result filters. Show active filters and matching counts where they apply. Make reset actions clear. Rename the checklist filter to explain what changes, or display actual task rows rather than hiding only their controls.

**Acceptance:** Test searching a device with no findings, selecting a priority with no matches, combined search/priority filtering, clearing search, and changing a task's state under an active filter. Users can predict which content is affected.

### UI-20 — Announcements and comparisons are detached from their device — P2, source-confirmed

Announcements occupy a separate lower section; comparison details occupy an earlier section. A reader must reconcile names, addresses and historical claims across locations.

**Fix:** Put matched announcements and recent observations in each device's “About this device” section, with explicit source/time/claim status. Keep unmatched announcements and earlier-only observations in a separate secondary area. Never turn an advertisement or old record into a current successful service check.

**Acceptance:** A reader can trace a claim to its device and source. Unmatched records stay unmatched, and facts from different dates are not silently combined.

### UI-21 — CVE content is too prominent when lookup is unavailable — P2, source-confirmed

`createCvePanel()` always renders an explanatory CVE section. Ineligible services receive another paragraph about missing software fingerprints and Deep scanning, plus an external database link and attribution. This adds substantial advanced content even when it cannot answer the user's question.

**Fix:** Put advanced published-software-problem research behind an appropriately labelled disclosure. Surface a compact availability/status line and any meaningful saved research outcome; keep the full limitations, privacy notice and attribution available. Do not invent CVE matches from a port or present research candidates as confirmed vulnerabilities.

**Acceptance:** Ineligible, eligible, checking, unavailable, no-match and saved-match states have distinct short summaries. No external request runs merely by viewing the report.

### UI-22 — Page shell, branding and navigation are inconsistent — P2, reproduced

Dashboard and reports say “NetGuard AI”; Settings and Saved reports use a large “Network Assessor” heading and browser-default-looking navigation. The latter pages have generic document titles. Separate templates own these shells, making global fixes easy to miss.

**Fix:** Share a consistent header, navigation, main landmark and footer. Use the actual page title as the principal heading and indicate the current page. Give parallel scan/report tabs distinguishable document titles, such as scan type and saved title/time, without making security claims.

**Files:** `app/templates/base.html`, `app/templates/dashboard.html`, `app/templates/scan.html`.

**Acceptance:** Moving between results, history and settings feels like one app. The user can return to the starting page, identify their current page and distinguish simultaneous tabs.

### UI-23 — Button, link and field styling is not shared across pages — P2, reproduced

Settings/history have plain native buttons while report actions use custom styles. Ordinary links inherit the browser's dark-theme link colour while some others have explicit teal/muted styles. The sampled Chromium link colour was readable against the dark base, so this is not a demonstrated global contrast failure. Input boundaries are very subtle; their recognition/non-text contrast needs a dedicated review.

**Fix:** Define shared button/link/field tokens, including normal, hover, focus, disabled and visited states. Preserve underlines or another non-colour link cue. Assess actual gradients and state combinations rather than assuming the entire dark palette fails or passes. [W3C: Contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

**Acceptance:** Components share consistent treatments and verified applicable contrast. Disabled controls remain understandable with a nearby reason.

### UI-24 — Forms need clearer grouping and contextual editing — P2, source-confirmed

Labels and controls are separate children of a generic form grid, with equal gaps within and between fields. Nickname/title edits use browser prompts; Settings errors use alerts. Scope settings show a disabled editable-looking range in automatic mode; advanced options and verbose status text share the same long form. Local nickname feedback is primarily posted back at the report header, far from the edited card.

**Fix:** Group each field's label, hint, control and error. Use an inline editor or properly labelled dialog for nickname/title changes, with visible limits, Cancel/Save and contextual save/conflict feedback. Keep automatic effective scope visibly read-only and distinguish it from a manual range and a server override. Put advanced settings into a named optional section. For validation, pair an error summary with field-level messages; retain the user's input. [GOV.UK: Error summary](https://design-system.service.gov.uk/components/error-summary/).

**Acceptance:** Editing and correcting errors works without native prompt/alert dependence. Confirmations and conflict states are visible where the user is working, with a clear focus return path. Safety/authorisation confirmation is retained.

### UI-25 — Loading/error/empty states need a consistent presentation contract — P2, recommendation

These are not all newly reproduced failures. The current system has multiple readiness, progress, AI, annotation, identity and scan states. They need a common vocabulary and placement so “no results”, “no match”, “could not check”, “still checking” and “no saved reports” cannot be mistaken for one another.

**Fix:** Define per-component loading, empty, unavailable, error, stale and success states. Show short local status feedback with an actionable recovery route. Keep factual reports readable when AI or name/CVE services are unavailable. Distinguish overall scan completion from personal checklist completion.

**Acceptance:** Synthetic fixtures cover each state. Refresh preserves the correct job/report, selection and edits. Errors do not erase readable evidence or falsely claim completion.

### UI-26 — Accessibility needs narrower live regions and bypass navigation — P2, source-confirmed risk

The templates lack a skip-to-main link. Both the entire findings list and entire detail pane are live regions, in addition to many smaller status regions. A selection can replace substantial text; actual screen-reader announcement behaviour was not measured in this review.

**Fix:** Add a visible-on-focus skip link with a valid main target. Keep actual status announcements short and local instead of announcing large prose replacements. Associate selection triggers and revealed content, use native disclosure semantics where appropriate, and verify the dialog keyboard contract. Do not add ARIA tabs unless implementing their actual keyboard pattern. [GOV.UK: Skip link](https://design-system.service.gov.uk/components/skip-link/), [W3C: Status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html), [W3C: Disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/).

**Acceptance:** Keyboard-only and screen-reader users can bypass navigation, select a result, hear a concise meaningful update and reach its detail. No focus is fully covered by app-created sticky content. [W3C: Focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html).

### UI-27 — Long-report density and default expansion need deliberate design — P2, reproduced/recommendation

At 768 pixels, device cards are expanded by default and the grid has two columns. The saved Light report measured 16,027 pixels high, longer than its 14,286-pixel 390-pixel version where device cards collapse. At 320 pixels it measured 16,084 pixels. A 200% root-font simulation at 390 pixels measured 37,048 pixels. Length alone is not a failure, but these numbers show why simply fitting the viewport is not enough.

**Fix:** Default to compact device summaries across sizes, expand on demand, and provide simple sorting/search/jump links. Consider paging or a Show more mechanism for very large device lists; prefer it to complex virtualisation until performance requires that complexity. Maintain discoverability, keyboard order and counts when reducing density.

**Acceptance:** Use 0/1/24/100-device fixtures. A reader can locate a particular device and return to it without repeatedly navigating a wall of expanded reports. All content remains accessible; no silent cutoffs are added.

### UI-28 — Current tests and frontend organisation miss these failure classes — P3, source-confirmed

Existing responsive tests check document overflow, expected content and dialog bounds. They did not catch internal 24-pixel checklist placement, the Clear-search/control-height mismatch or lost finding focus. The stylesheet has separate overlapping 620-pixel sections, earlier/later hero overrides and scattered component rules. `scan.js` combines state, fetching, rendering, events, editing and large generated content structures; its selected-item handler also renders the detail twice.

**Fix:** Add task-based and component-geometry tests, then extract cohesive report components and consolidate responsive rules. Keep one state owner and stable identifiers. Do not remove code merely because it looks unfamiliar, rename persisted fields, or redesign annotation/nickname concurrency as part of visual cleanup.

**Acceptance:** Tests fail on the reproduced defects and pass on the eventual fix. Changes to one component do not alter unrelated layouts or reset filters, selection, disclosures, focus, saved revisions or evidence.

## Proposed information structure

This is a starting design to validate, not a demand to replace everything with tabs or another framework.

```text
Consistent header: NetGuard AI | Scan | Saved reports | Settings

Report overview
  Saved date + Light/Deep + scan status
  Discovered / checked / could not check
  Review-priority counts + short limitation / self-check note when relevant
  Recommended first task + contextual retry if checks could not finish

Your devices
  Search + clear scope + matching count + simple sort/filter
  Consistent summary rows/cards
    Name/nickname + address + source qualification
    Check status | observed features | review items/priority
    View details | secondary rename/identification controls

Device detail / selected review item
  What answered → What it means → What to check next
  What remains unknown
  All features (plain labels, expandable)
  About this device (name/model/source/confidence/history)
  Supporting details (technical evidence, original wording, eligible CVE research)

Your review tasks
  Complete task list or explicitly labelled suggested first tasks + Show all
  Short status controls + local save feedback

Optional comparison / unmatched announcements / technical export
```

For Light, test whether readers prefer device-first or priority-first entry. For a single-device Deep report, go directly from its compact overview into that device's details; do not repeat a whole network-oriented device section unnecessarily. Every device must remain accessible even when it has no findings.

### Component specification

- **Device summary:** one outer boundary; stable identity/status/count/action slots; rich information expands within the same device context. Show unavailable values honestly instead of dropping labels and moving other fields. Expanded bodies have natural height.
- **Review item:** readable title, intact priority badge, clear device/feature context, clear selected state. On mobile the explanation appears next to the trigger or in a dedicated recoverable detail view.
- **Action:** one instruction, a short labelled status control, contextual saving/saved/error/conflict feedback. Keep the distinction between a personal review note and verified remediation.
- **Technical/AI information:** one supporting disclosure pattern, not multiple competing paragraphs before the useful action. Critical limits and incomplete coverage stay visible.
- **Forms:** consistent field groups, hints, errors and action groups; no unexplained disabled choices.
- **Spacing proposal:** tokens for 4/8/12/16/24/32/48 pixels, used according to component relationships. Prefer 8–12 pixels between peer controls, 16–24 between component parts and responsive larger section gaps. Test these choices; do not use arbitrary margins to compensate for incorrect layout ownership.
- **Typography proposal:** readable body and secondary sizes, short headings, moderate line lengths, no all-caps paragraphs. Preserve text resizing and user text-spacing overrides. WCAG text-spacing checks alter line, paragraph, letter and word spacing without losing content/functionality. [W3C: Text spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html).

### Browser-only feasibility check

Temporary CSS moved the checklist into column 2 and made its label a grid; at 390 pixels the inspected checklist/select became 262 pixels wide instead of a 24-pixel container with overflowing controls. A non-shrinking priority cell kept Medium intact. Flexible search sizing contained Clear search. Giving device groups one boundary and a bottom-aligned secondary action area aligned the first desktop row's toolbars at the same vertical position.

These prototypes are intentionally incomplete. They do not resolve mobile detail placement, focus loss, excessive prose, full task discoverability or the preferred long-list structure. Screenshots named `prototype-*` are proposals, not evidence that the running app has been fixed.

## Execution plan for the next development pass

1. **Add reproductions first.** Browser assertions for checklist column/containment, Clear-search bounds, intact badge, selected-item keyboard focus and immediate mobile detail access. Include both sparse and rich reports.
2. **Fix local layout and interaction defects.** UI-01–06. Preserve stable finding/action/device identities; remove the duplicate detail render. Verify no scan request or external lookup is triggered by navigation.
3. **Standardise components without changing factual data.** UI-07–12, 22–24: common shell, device anatomy, shared field/button/disclosure styles and local editing feedback. Preserve the current visual identity.
4. **Restructure content for the home-user tasks.** UI-13–21 and 27: compact overview, direct result detail, complete plain-language feature access, explicit task coverage, contextual naming and announcements, secondary comparisons/CVE research. Validate device-first versus priority-first with readers.
5. **Consolidate implementation.** UI-28: organise CSS by tokens/base/components/responsive states; extract cohesive rendering modules after behaviour is pinned by tests. Avoid a sweeping rename/refactor that changes persisted contracts.
6. **Verify accessibility and all states.** UI-25–26: keyboard, screen-reader, zoom, text spacing, contrast, target exceptions and loading/error behaviour. Add clear results to the testing/evaluation record.
7. **Run a nontechnical-reader study.** Use sanitised saved/synthetic reports first; a live network scan is not needed to assess layout. Only do later live checks on a newly confirmed authorised network/target. Do not claim a home scan proves the interface understandable.

## Verification checklist and reader tasks

- Baseline: 320/390/768/1024/1440-pixel viewports, portrait and short landscape; Chromium, Firefox and WebKit; real 200%/400% zoom separately from text-size simulation.
- Content: no devices, one device, many devices, rich/empty optional data, very long/duplicate/unnamed names, conflicting and historical names, unavailable source/time, failed target, zero findings, many findings, more than five services, precise/ineligible CVE fingerprints.
- State: queued/running/analysis/finished, incomplete/cancelled/failed scan, AI unavailable/partial/ready, annotation save/conflict/recovery, name lookup unavailable, CVE unavailable/no-match/saved matches. Use synthetic responses for failure cases.
- Geometry: child controls inside their intended component and grid cell; no clipped badges, overlapping targets or misassociated actions. Technical-table overflow is local and explicitly labelled.
- Keyboard: skip to main, select result, navigate to explanation and back, use filters and checklists, open/close rerun/edit dialogs, retain focus on saves/rerenders and restore it after navigation.
- Accessibility: manual target/spacing exceptions, text/state contrast, labels/descriptions, meaningful heading order, concise live announcements, visible/unobscured focus, reduced motion, user text-spacing settings.
- Data invariants: no invented identity/CVE/severity/coverage, no removed evidence, no implicit rescans, no annotation-as-security-success, revision-safe concurrent edits, nickname consistency across pages, readable reports without AI or optional enrichment.
- Reader tasks: “Which device should I look at first?”, “Why is this name shown?”, “What did not finish?”, “What does this feature do?”, “Does this mean someone accessed my files?”, “What should I do without disabling something important?”, “Where are my remaining review tasks?”, “What does marking Checked actually mean?”
- Record task completion, interpretation errors, time to locate information, assistance needed, and perceived confidence. Establish acceptance targets before evaluating; do not invent pass percentages without a study.

The first deliverable should be a small, tested presentation fix, followed by consistent device/result components. A cosmetic redesign alone would leave the most consequential interaction and information-structure problems unresolved.
