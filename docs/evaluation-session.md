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
