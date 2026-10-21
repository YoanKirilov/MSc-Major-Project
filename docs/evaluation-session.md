# Nontechnical-reader session kit

Status: prepared protocol, not a completed study. Follow the university's ethics and
consent requirements before recruitment. Use anonymous IDs and synthetic reports only;
do not collect participants' home addresses, device identifiers or passwords.

## Facilitator preparation

Use the same saved synthetic facts for both conditions: original rule-based wording
and validated Ollama-selected wording. Record model, prompt version and report version.
Keep layout and questions identical. If AI falls back to original text, record that
condition rather than claiming an AI rewrite. Do not run scans during the session.

Important control: the normal report interface now prefers accepted AI-selected
fields, but uses reviewed editorial alternatives for other fields. It is therefore
not an original-versus-AI experiment by itself. Prepare and independently check fixed
synthetic views of (A) stored original guidance and (B) actual validated model output.
Record unchanged/model-fallback fields separately rather than attributing them to AI. If
evaluating the ordinary interface instead, label it a combined-interface evaluation,
not evidence that Ollama alone improved comprehension. These controlled views still
need to be prepared before recruitment; this document does not implement them.

Use the project targets and limitations in [the quality plan](quality-plan.md).

Alternate which condition participants see first. Rotate scenario order to reduce
learning effects. Do not explain technical terms until the participant has answered;
record requested help. Stop if the participant wishes to withdraw.

## Participant instructions (read aloud)

We are testing the report, not your computing ability. Read it as if it described your
home devices. Please say what you think it means. Do not change any real device settings.
You may skip a question or stop at any time.

For each report ask:

1. What did the scan find?
2. What does it leave unknown?
3. What would you do first, and why?
4. Does it prove a device is safe or has been hacked?
5. What wording was confusing? Rate clarity from 1 (unclear) to 5 (clear).

## Synthetic scenarios and scoring guide (facilitator only)

| Scenario | Observation | Essential limitation | Sensible first action |
| --- | --- | --- | --- |
| Device web page | An HTTP service answered | No proof of compromise or that every page lacks protection | Identify the device and review its web/security settings |
| Zero findings | Selected checks finished without review items | Other services/settings were not fully assessed | Review scope; do not conclude everything is safe |
| No responders | No devices answered discovery | No device security assessment was possible | Check connection and authorised scope |
| Incomplete scan | One device checked; another timed out | The unfinished device remains unassessed | Review saved findings and retry the unfinished device |
| Model unavailable | Scan evidence and reviewed fixed wording remain readable | Wording provenance does not establish device safety; no outage banner is expected | Use the visible guidance and inspect its source in Supporting information if needed |

Score questions 1–3 as 1 only if the relevant observation, limitation, or sensible
first step is recognised, otherwise 0. Question 4 scores 1 only if neither safety nor
compromise is claimed as proven. Keep verbatim anonymous answers to support scoring.
Ask a second reviewer to independently score a sample and record disagreements.

Record one row per participant/condition/scenario in `evaluation-results-template.csv`.
Time includes reading and questions 1–4. Summarise comprehension (0–4), unsafe
interpretations, time and clarity separately. Small samples are exploratory; higher
clarity ratings alone do not demonstrate better understanding. Report withdrawals,
missing answers and unchanged/fallback AI wording explicitly.

## Library and target-selection tasks (added 1 October 2026)

These are combined-interface tasks, not an AI-only experiment. Use synthetic saved
reports and do not actually start a network scan. Ask the participant to:

- Find a named device's earlier report, then explain the difference between no search
  matches and an unreadable saved report. A storage warning is not a security finding.
- Select a device for Deep, refresh the choices and identify the address that would
  be checked. Repeat after editing the address manually or removing it from the list.
- Explain what "Advertised its presence" and "Last device check timed out" tell them.
  Neither proves the device is currently present, safe, or the same device at that IP.
- Explain the first action in the report in their own words and identify what was
  not checked. Record confusing terms without coaching before their first answer.

For each task record success, help requested, time, mistaken target selection and the
participant's explanation. Keep these results separate from the existing 0–4 AI
comprehension score. No participant results have been collected by this change.

## Recovery, progress and earlier-observation tasks (7 October 2026)

Use synthetic reports and a held synthetic scan, never participant networks. Ask:

- After refreshing a running Deep page on a narrow screen, what is being checked?
  Can its target be changed now? Success: find progress and the fixed target without
  attempting a second scan. Record time, scrolling and requested help.
- A nickname recovery notice says the latest edits may be missing. What is affected?
  Success: distinguish labels from unchanged scan evidence; reload before editing.
- One device has a current name, one an earlier saved name and one no detected name.
  Which identities are proven? Success: none; names are clues and unnamed is not
  automatically suspicious. A user nickname is not a detected name.
- Explain “Seen earlier, not matched this time” separately from an unfinished device
  check. Success: absence is uncertain; an unfinished check remains unassessed. Do
  not call either a verified repair or a new vulnerability.
- This report checks the computer running NetGuard. Does an answering feature prove
  an internet user can reach it? Success: no; review the recorded limits and firewall.

Record each task separately from AI-only scores. A facilitator walkthrough or passing
browser tests is not participant evidence. Recruitment, ethics approval, controlled
original/AI views and independent scoring are still required before claiming results.

## Physical-device and platform checklist

Still pending: actual Android Chrome, iOS Safari, keyboard/screen-reader sessions and
the intended Ubuntu installation. Browser emulation on Windows is not a substitute.

On each physical device record OS/browser version, orientation and text-size setting.
Check touch targets, dropdown readability, the on-screen keyboard, warning announcements,
focus after refresh, search/reset/pagination, and Deep target preservation without any
scan submission. Use a deliberately configured authorised lab to serve synthetic UI
data; do not weaken the app's loopback/session protections just to access it by phone.

On Ubuntu, install the pinned runtime/dev dependencies in a new virtual environment,
run `python scripts/check.py --browser --browser-engines chromium,firefox,webkit` and
`python scripts/check_package.py`, and record exact results. A live Nmap check needs
separate authorisation of the connected network. No Ubuntu execution is claimed here.

## Revised interface tasks — 9 October 2026

These evaluate the combined interface from the [UI/UX implementation](ui-ux-implementation-20261009.md),
not Ollama in isolation. Use synthetic saved facts with rich/sparse device cards,
an unfinished target, an uncertain name and more than five answering features.
Do not coach the participant before their first answer or perform a live lookup.

- Find the device you would review first, then locate its explanation on a narrow
  screen. Record wrong-device selections, scrolling, assistance and time.
- Open **About this device** and explain why its name is shown. Success distinguishes
  a device claim, earlier name or personal nickname from a verified identity.
- Find a feature beyond the first five. Explain what answered and what remains
  unknown; answering does not establish that anyone used it or that it is vulnerable.
- Search devices without changing review-item search, then clear each search.
  Record whether scope/count labels prevent confusing no match with no findings.
- Find every remaining checklist action, mark one **Checked**, filter **Need help**,
  and explain that these are personal notes, not a new security test or verified repair.
- Rename a synthetic device, cancel a second edit and recover from a simulated save
  conflict. Success preserves the draft and makes the affected device unambiguous.
- Find the unfinished device and distinguish it from an AI wording outage. Neither
  can be interpreted as a completed check or a safe-device verdict.
- Find the published-software research disclosure and explain why a port alone is
  insufficient for a CVE match. Do not submit a real lookup during the session.

For each task record success, interpretation errors, help and completion time separately
from the original 0–4 AI score. Agree acceptance targets with the supervisor before
recruitment. No participant measurements or comprehension success rates are supplied
by this implementation. Include keyboard-only, physical-phone and screen-reader
sessions in the remaining accessibility work rather than treating emulation as a pass.

## New report-note tasks — 6 October 2026

Use only synthetic, saved reports with at least two identically named or unnamed
devices. Ask readers to identify which checklist control belongs to each device,
mark one action Checked, filter by Need help, then explain what the review-progress
count means. A correct interpretation distinguishes their notes from completed scan
checks and does not claim Checked proves safety. Reopen a different report and verify
that review statuses have not silently carried over.

For comparison, include separate first-report, missing adapter-address, different
profile and incomplete-check examples. Ask why each cannot be compared rather than
asking readers to guess whether a device is new or fixed. Include a self-check report:
ask whether a local answer proves internet exposure (it does not). Record mistakes,
help requested, clarity and task time separately from AI-only scoring.

On real phones/assistive technology, specifically check the labelled status dropdown,
announcement after a save failure, focus after name/CVE lookups, and text-size reflow
of address-specific labels. These are prepared tasks, not completed evaluations.

## Inclusive interface evaluation — 15 October 2026

Status: prepared, no participants recruited and no measured results. This extends
the combined-interface protocol above; it is not an AI-only comparison. Record
the application version and use the same synthetic facts and tasks across sessions.
Do not run scans, model requests or name/CVE lookups during a participant session.

Before recruitment, obtain the university's required ethics/consent approval and
agree success criteria with the supervisor using the existing quality targets.
Include disabled and nondisabled nontechnical readers, and readers with different
computing experience. Disability does not imply lack of technical experience.
Offer accessible consent materials, breaks and withdrawal without explanation.
Ask which accommodations/input methods help; do not collect diagnoses. Allow each
person to use familiar assistive technology rather than teaching an unfamiliar tool.
One person cannot represent every user with the same accessibility needs.

Use the header-only [UI task log](evaluation-ui-tasks-template.csv) separately from
the existing original-versus-AI comprehension scores. Use anonymous participant IDs,
record browser/OS/assistive-technology versions only with consent, and follow the
agreed storage/retention plan. Never record household identifiers, passwords or real
network reports. Collect screen/audio recordings only with separate explicit consent.

| Task | Participant prompt | Facilitator success check |
| --- | --- | --- |
| UI-01 | Find the device that needs checking first. What remains unknown? | Finds review/unfinished counts; does not infer online status or safety from the saved card |
| UI-02 | Save a room label, then cancel another change. | Recognises personal labels; saved state and cancelled draft are distinct from scan facts |
| UI-03 | Open this device's earlier report and return to your place in My devices. | Correct device opens; Back preserves search/page; no device/address transcription needed |
| UI-04 | This old device link cannot be matched. What can you still read? | No substitute device is guessed; the full report remains available |
| UI-05 | Make the text larger and use your device's colour preference. | Choices agree in Settings/report; distinguishes applied from remembered when storage is blocked |
| UI-06 | Explain one technical word, switch topic, close the information window and continue reading. | Finds topic selector, scrolls its content, closes and resumes with usable focus/page position |
| UI-07 | Mark an action Checked, then explain what that means. Repeat with a simulated failed save. | Personal note is not a verified repair; notices one useful outcome and retains/recover draft |
| UI-08 | Delete an unwanted synthetic report and recover it. | Confirmation is understood; Undo/recovery succeeds without deleting another report |

Present completed, unfinished, unnamed, zero-review-item and AI-unavailable examples.
Ask what was found, what remains unknown and what to do first without coaching.
Record unsafe interpretations explicitly, including claims of verified safety,
confirmed intrusion, device presence or automatic repair. Preserve essential HTTP
precautions in any example that involves opening a device page.

For each task record completion, wrong-device selection, assistance, confusing
words, unsafe interpretation, time and clarity separately. Do not combine these
into a new success threshold after seeing the results. Have an independent reviewer
check a sample of anonymous responses and record disagreement. Report missing data,
withdrawals, untested configurations and sample limits; a small exploratory study
does not establish that everyone understands the product.

### Manual accessibility checks still required

- Keyboard: skip link, predictable tab order, visible unobscured focus, native
  disclosures, every search/save/recovery action, no trap outside an open modal.
- Screen reader: headings/landmarks, label-in-name, table relationships, useful
  validation, one meaningful save/error announcement and correct dialog focus return.
  Record actual speech observations; DOM roles alone do not establish spoken output.
- Voice input: controls can be invoked by their visible labels; repeated controls
  have usable device context without unrelated hidden names.
- Magnification: actual browser zoom at 200%/400%, user text spacing, forced colours,
  long labels and short landscape windows; focused controls remain reachable.
- Physical Android/iOS: touch, orientation, device text settings and the on-screen
  keyboard. Do not expose private app APIs or weaken loopback/session protection
  to obtain a phone screenshot; use approved isolated synthetic deployment.

Record issues, implement the smallest justified fixes and repeat affected tasks.
Automated Chromium/Firefox checks and simulated viewports complement these sessions;
they do not replace participants, actual assistive technology or a full conformance
assessment. See [WAI involving-users guidance](https://www.w3.org/WAI/test-evaluate/involving-users/).

## First-action and inclusive evaluation - 18 October 2026

Status: prepared tasks, not collected results. Use the combined-interface condition
unless independently prepared original/model views satisfy the controls above.

- Read the short first step without opening **Why start here?**. Explain what to
  do and identify the visible precaution. Then open the explanation and say what
  it adds. Score action, uncertainty and precaution separately; brevity alone is
  not success. Include a self-check and an unfinished-device example.
- Read a CVE example with related references but no usable product mapping. Explain
  whether a vulnerability was confirmed. Inspect a synthetic **Maker's advice**
  destination without navigating to a real device or changing settings. Success
  distinguishes database leads from a verified device vulnerability.
- With actual NVDA/Firefox or VoiceOver/Safari, lose a synthetic CVE reply and
  reload saved references. Repeat an unchanged name lookup. Record the final
  announcement, focus location and any duplicate/stuck waiting message. A DOM
  `role=status` check is not evidence of actual speech.
- At true 200%/400% browser zoom, with forced colours and keyboard-only input,
  open/close Supporting information and use search, edit and recovery. Record
  clipping, obscured focus, reading order and whether every control remains usable.
- Disable JavaScript in the synthetic app and explain why scanning/report loading
  is unavailable and how to recover. No scan should start; existing results should
  not be described as lost. Repeat a deliberately blocked report module.

Record browser/OS/AT versions, settings, anonymous task results and consent status.
Use the earlier checklist for voice input, switch access and physical phones. No
participant, physical-device, true-zoom or real-screen-reader pass is asserted by
the automated 18 October changes.

## Naming and recovery tasks - 19 October 2026

Status: prepared only. Use synthetic saved examples, not participants' home data.
Keep technical lookup details optional; do not add controls merely for evaluation.

- Show two unnamed devices: one with no name returned, another with a timed-out
  name source. Ask whether either is an intruder or absent, and what the difference
  means. Success preserves uncertainty; a later name is still a claim, not identity.
- Show a queued check that expired and a deliberately excluded address. Ask which
  targets **Retry unfinished checks** would check. It should include the eligible
  unfinished device, not repeat completed work or probe excluded/silent addresses.
- Show a CVE record with unusable applicability information. Ask whether a matching
  vulnerability was ruled out. Success distinguishes unknown coverage from a usable
  mapping with no related results, and neither is a safety verdict.
- With actual assistive technology, show one backend-version notice. Check that it
  is announced without moving focus or hiding saved evidence, and the instruction
  to finish active scans before restarting is understood. Do not deliberately
  interrupt real scans to create this condition.
- Simulate a lost CVE reply followed by another tab's cached lookup. Use saved
  reference recovery and record whether the outcome is understood without sending
  another research request. Explain any attempt too old for the bounded receipt
  history as unconfirmed, not a proved failure or successful retry.

Use the earlier consent, anonymous task log and real-AT/phone checks. These tasks,
DOM assertions and automated keyboard tests are not collected participant data or
evidence of spoken screen-reader output.

## Scan-start recovery and shorter wording - 21 October 2026

Prepared only; no participant results have been collected. In an isolated synthetic
session, lose a scan-start reply, then refresh while the original start is being
confirmed. Ask the reader what **Check original scan start** does, whether Scan is
available, and whether **Return to scan setup** itself starts a replacement. Success:
the check reads the original attempt, uncertainty is not proof of failure, and
returning to setup requires a separate explicit choice to start another scan.
Repeat using an unfinished-device retry and ask which addresses will be checked.

Compare the shorter gateway label and unknown-CVE message with their optional
technical evidence. Ask what is known, what remains unconfirmed, and the next safe
action. Use actual screen-reader speech/focus and nontechnical readers, not just DOM
assertions. Keep recruitment, consent and anonymous task outcomes in the study kit;
automated tests cannot establish comprehension or accessibility certification.
