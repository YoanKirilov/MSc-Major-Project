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
| AI outage | Scan evidence saved; simplification unavailable | AI failure is not a failed network check | Read rule-based guidance or retry explanation without rescanning |

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
