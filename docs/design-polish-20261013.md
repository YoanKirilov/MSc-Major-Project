# Combined usability improvements — 13 October 2026

## Scope and execution plan

Implement the remaining findings from `home-progress-position-20261013.md`, plus
small related usability faults found in this review. Retain the current visual
design, both palettes, stable below-setup progress and empty-start/one-entry history.
Do not run live scans or contact AI, CVE, Pi-hole or other device-data providers.
Use isolated JSON folders, mocked services and synthetic browser fixtures only.

1. Correct readiness/running/reconnecting/cancellation copy; retain the same pinned
   job on failure and refresh. Make missing Deep-address errors visible beside and
   programmatically associated with the input; keep server validation authoritative.
2. Space and wrap progress/other-job actions. Give the visual progress indicator
   task-progress semantics, with indeterminate single-device/discovery/wait stages.
   Explain that stage progress is not a remaining-time estimate; retain throttled
   polite stage announcements and reduced motion.
3. Expose existing browser-local display preferences consistently from navigation
   and immediately in Settings, independently of backend settings availability.
   Keep the convenient report preferences too; do not require Save settings.
4. Shorten native recent-device options to name + address; display saved check/date
   context beside the selected device, distinguish earlier evidence from current
   connectivity and preserve manual input during refresh/error/racing replies.
5. Add end-of-list history paging/retry controls without fetching on initial open,
   search or reset. Preserve exactly one requested entry and ordinary-scroll focus.
6. Separate always-visible report tools from conditional recovery actions. Make
   the first useful review action visually primary instead of encouraging another
   scan first. Simplify explanation-outage wording without concealing fallback or
   removing provenance from supporting details.
7. Verify controller state, keyboard focus, error/end states, names, static assets,
   both themes, enlarged text and narrow/tall layouts. Run the full offline gate,
   proportionate three-engine browser checks and an offline installed-package check.
   Record failures and retests honestly; no accessibility certification is inferred.

## Design references

Status updates must be understandable to assistive technology without stealing
focus. [W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).
Task completion uses progressbar semantics rather than a meter.
[W3C progressbar versus meter](https://www.w3.org/WAI/ARIA/apg/patterns/meter/).
Errors should identify the affected field and explain the problem in text.
[W3C error identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html).
Group related actions and distinguish primary from secondary actions.
[GOV.UK buttons](https://design-system.service.gov.uk/components/button/).
Keep selectors and nearby hints understandable, and do not replace native controls
with a complex custom widget without evidence of need.
[GOV.UK select](https://design-system.service.gov.uk/components/select/).
Keyboard navigation should follow a meaningful sequence.
[W3C focus order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html).

## Implemented changes

- Dashboard messages now distinguish starting, queued, running, preparing explanations,
  reconnecting, cancellation and read errors. They do not continue saying Ready while
  a job is selected. Unchanged live-region copy is not rewritten on every poll.
  A failed cancellation retains the same pinned job and a usable retry action;
  capacity waiting no longer immediately replaces its message with Ready.
- A missing Deep address has associated inline error text, `aria-invalid` and input
  focus. Typing or choosing a saved device clears that error without submitting a
  scan. Backend validation and explicit authorisation remain authoritative.
- Scan and other-job actions use wrapping, spaced groups with 44-pixel minimum
  targets. Progress stays below setup with no forced start/reconnect scroll.
- The graphical bar is a labelled `progressbar`, associated with its stage context
  and not-time-remaining explanation. Queued/discovery/one-device checks omit a
  numeric ARIA value; numeric stage progress is bounded. Existing polite milestone
  announcements, reduced motion and factual coverage remain.
- Every shared header links to visible Display preferences in Settings. Dark/Light,
  text size and movement choices apply immediately and remain usable during saved
  settings outages or blocked browser storage. Report preferences are retained.
- Recent-device options contain name + address; selected saved status/date appears
  separately and is not represented as current connectivity. Cached context updates
  after restoring an immutable target. Manual input survives refresh, empty results
  and outages; malformed responses do not discard earlier usable choices. Descriptive
  messages are not unnecessarily rewritten for unchanged manual input.
- Both history paging controls mirror loading/retry/end state. The companion appears
  after revealed entries and supports Tab/Enter without backtracking. Reset still
  prepares an empty list without a request. Explicit loading of an unreadable warning
  focuses that warning locally; ordinary scrolling never steals focus.
- Report recovery buttons stay visible when relevant, in a separate action group.
  Run again is secondary; the first useful review action is primary. Explanation
  outage/retry wording is simpler, while supporting details retain model/fallback
  provenance and the JSON evidence is unchanged. Recovery controls default to
  visible layout even when a browser cannot parse the newer `:has()` selector;
  that selector only removes empty groups in supporting browsers.

These changes extend existing modules and reuse spacing/theme tokens; no replacement
framework, custom combobox, new scanner, model, database or stored-result migration
was introduced. Existing report profile colours and empty-start history remain.

## Verification and limits

The complete isolated offline gate passed **602 Python and 158 JavaScript tests**,
lint, formatting for 150 files and seventeen module syntax checks. Artifact:
`.test-artifacts/checks-fcabd987d4/`. The earlier checks-c35f5f2302 also passed before
the final recovery-layout fallback; the final source passed focused Ruff/format/
whitespace checks again after browser-contract corrections.

Final offline installed-package verification passed **six pages, eighteen assets,
demo read/create/reopen and both dependency checks**. All **93 application files**
match the installed wheel byte-for-byte. Artifact:
`.test-artifacts/package-6d4a073c0d/`. The earlier package-8fd6ad4ee2 passed installation
but was not final: the defensive picker guard changed during its build, producing
one source mismatch. Package-1464470bb7 matched its source before the final CSS
fallback; the latest package supersedes both as final evidence.

The initial combined browser run found two failures in the new progress test:
the fixture had already opened `/`, so a fragment-only navigation did not rerun
dashboard modules. The test now reloads after setting the pinned URL. The corrected
progress test passed in Chromium and Firefox with no application source change:
`.test-artifacts/design-polish-progress-retest-20261013/`.

The broader Chromium/Firefox run retained **148 passes, four failures and one
teardown error** over nineteen minutes. Artifact:
`.test-artifacts/design-polish-final-20261013-results.xml` and its associated folder.
Two failures were the fragment-only progress test described above. The other two
expected old text: status inside a picker option was now correctly in the selected
device description, and the explanation-outage notice had intentionally become
plain English. The picker expectation now asserts the actual selected address's
saved status, not another option's status. The workflow also needed its later
missing-address expectation aligned with the new field-associated wording.

Final affected retests passed:

- **Eight design browser cases** in Chromium/Firefox, including labelled progress,
  accurate state, address-error focus, grouped report recovery, Dark/Light/narrow
  layouts and simulated absence of `:has()` layout support.
  `.test-artifacts/design-polish-design-final-20261013-v2/`.
- **Three contract/cleanup cases** passed: the complete saved-report editing,
  nickname sync and native picker task; and both engines' scan-purpose/coverage
  disclosure task. `.test-artifacts/design-polish-contracts-final-20261013-v2/`.
  Its workflow case reached one further old validation-text expectation; this
  failure is retained, not counted as a pass.
- The corrected **complete synthetic scan → details → AI wait/outage/retry →
  report/history → Light/Deep Run again workflow** passed separately with no new
  real probes or models. `.test-artifacts/design-polish-workflow-final-20261013/`.

The broad run's teardown error was the existing Windows Proactor socket-reset
callback (`WinError 10054`) followed by its isolated Uvicorn thread not ending
within the fixture's fifteen-second join. The same Chromium task and its Firefox
counterpart both passed on focused rerun; no callback was suppressed, timeout
relaxed or application runtime workaround introduced. Treat the underlying
Windows lifecycle reliability as a remaining runtime investigation, not a UI
failure proven fixed by this work.

The broad command was **not** repeated wholesale after the small test corrections
and CSS fallback. Its original failures remain visible; final offline, package,
all affected browser retests and the broad unaffected passes are separate evidence.
Visual inspection of synthetic progress in Dark desktop/Light phone layouts confirms
below-setup order, accurate saved-results status, spaced actions and readable wrapping.
Report-header screenshots at 320/1440 pixels also show explicit incomplete coverage,
visible recovery controls and secondary report tools. A separate read-only peer
review found no new state, keyboard or coverage blocker in the frozen source.

**WebKit is currently unverified, not passed or skipped as a successful case.**
New appearance/picker cases failed before a page existed with TargetClosedError;
an independent blank-page probe reproduced the issue. The installed dependency
checker reports Windows Application Control blocking `WebKitWebProcess.exe`;
CodeIntegrity events 3077/3033 corroborate the policy block. Microsoft's primary
documentation identifies 3077 as an enforced-policy block and explains the paired
3033 event. [Microsoft App Control event documentation](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/event-id-explanations).
No policy, allowlist, browser installation or operating-system security setting was
changed or bypassed. Use an approved test environment or administrator-reviewed
allowlisting for later WebKit validation; current Chrome/Firefox results cannot
establish Safari compatibility on physical devices.

No live Nmap scan, real device check, Ollama generation, CVE/Pi-hole lookup or normal
saved-data write is part of this work. Workflow checks use isolated synthetic jobs
or mocked reads; fixture guards reject real scanners/providers. Physical devices,
screen readers and a study with nontechnical readers remain evaluation work, not
features claimed completed by automated tests.
