# Live Light/Deep check and UI/UX review - 14 October 2026

## Scope and method

The user requested live checks of both scan options, issue recording, and a
parallel research review of current UI/UX practices. No application fixes were
requested or implemented in this turn. Existing unfinished workspace changes were
preserved. The separate [UI/UX recommendations](ui-ux-recommendations-20261014.md)
contain eleven prioritised proposals, primary-source references and acceptance
checks; they distinguish source findings, evaluation risks and product choices.

Windows detected the previously authorised home range `192.168.0.0/24` and this
PC at `192.168.0.216`. The Light scan used that range; Deep targeted only this PC.
Nmap reported 7.991, Python 3.14.2, and local Ollama `llama3.2:3b` was available.
The new scan pair ran through the actual app UI/API and normal runtime interpreter,
but an owned loopback backend and fresh private data folder isolated test evidence
from normal history. Existing scanner settings were read, not edited. The test
retained raw XML and used automatic scope selection with mDNS enabled. Pi-hole
was not used, and no external CVE lookup was requested.

Private artifacts: `.test-artifacts/live-review-20261014-b/`. Scan records are
not silently added to normal Saved reports. Do not publish private reports,
screenshots, host names, MACs or bootstrap/backend logs from this ignored folder.

The reusable opt-in Windows check is:

```powershell
.venv-quality\Scripts\python.exe -B scripts/live_review.py --authorised --scope 192.168.0.0/24 --host 192.168.0.216 --artifacts .test-artifacts/<new-private-folder>
```

Reconfirm the current authorised network and this-PC address before another run.
The command rejects a changed scope/address or a reused output folder. It retries
only GET connection-reset errors, never scan submissions. Failure cleanup requests
cancellation only for its own jobs and leaves the owned backend alive if active-job
cleanup cannot be confirmed. The normal backend is not stopped by the helper.

## Completed live results

| Measure | Light home range | Deep this PC |
| --- | --- | --- |
| Finished device checks | 11 of 11 discovered | 1 of 1 selected |
| Answering features | 10 | 14 |
| Review items | 7: three Low, four informational | 4 informational |
| Scan errors / failed checks | 0 / 0 | 0 / 0 |
| Time through Ollama | 425.3 seconds | 533.4 seconds |
| AI records ready and revalidated | 8 | 5 |
| Rule-based fallback / rejected fields | 0 / 0 | 0 / 0 |
| Automatically reported names | 1 of 11 | 1 of 1 |
| mDNS observations | 2 | 0 |

Light ID: `8755474c-e2e2-474f-9a52-dff9aef6688b`.
Deep ID: `44c3cb82-019d-41f3-a404-f0c4b3b845ef`.

Raw XML replay matched 165 Light and 21 Deep service records and all eleven
deterministic findings. No completed check lacked its retained raw XML. All thirteen
accepted explanation records were checked against their reviewed factual choices;
selected AI inputs contained no recorded IPs, host names, MACs, scan range or raw XML.
This validates the stored transformation, not vulnerability detection accuracy or
participant comprehension. Review items are not confirmed vulnerabilities or a
network security score.

Deep's only warning was `SELF_SCAN_LOCAL_ROUTING`, an expected Windows self-check
limitation, not a failed check. A program replying to this computer does not prove
that another device or the internet can reach it. The report displayed that warning.

## Live browser and storage checks

- Exactly two scan submissions occurred in the successful pair. Refreshing each
  in-progress page retained its own job; neither refresh submitted another scan.
- Both pages automatically opened their saved report after the analysis phase.
- Chromium displayed both actual reports at 320, 390, 768 and 1440 CSS pixels:
  eight profile/viewport combinations, with no page errors or horizontal page
  overflow. Full-page screenshots and rendered text were saved privately.
- The raw-data/model audit was read-only. The helper's backends no longer listen
  on their test ports. The normal app remained on 8765; its PID changed independently
  during the test, and the helper never stopped it.
- All 608 files from the initial, pre-attempt normal-report baseline remained
  byte-identical. The later baseline's `normal_existing_reports_unchanged: false`
  result is retained, not overwritten or called a pass: an independent normal
  scan was created before the second test pair and finished during it, naturally
  changing that report's `scan.json`, `summary.json` and `progress.json`. No files
  were missing. Investigation is recorded in `normal-integrity-investigation.json`
  and `initial-baseline-integrity.json`. Test requests and writes used the separate
  test backend/data folder, not normal scan creation endpoints.

This was an actual Chromium report check, not a new all-engine, physical-phone,
screen-reader or human-study evaluation. Earlier Windows WebKit policy restrictions
remain a limitation; they were not bypassed.

## Issues and limitations observed

1. **Running-instance/source mismatch, resolved during the session.** Initially,
   port 8765 served all current static assets but its OpenAPI schema did not list
   the new report Delete/Undo routes. This is consistent with an older Python
   process serving files changed in place. In the second attempt both routes were
   present, and normal PID changed to 8460. The helper did not restart that instance.
   Future releases should expose a build/capability check and actionable restart
   guidance rather than silently disabling controls when metadata is missing.
2. **First live harness attempt interrupted by a local HTTP reset.** Attempt
   `.test-artifacts/live-review-20261014-a/` failed on a Playwright progress GET with
   `socket hang up`. The first Light/Deep records were safely cancelled and preserved,
   not reported as complete. No corresponding scanner exception was in the backend
   log. A stale keep-alive connection is a possible cause, not proven root cause.
   The helper now permits two connection-reset retries for GET only. The fresh
   complete pair passed. Across both attempts four scan submissions occurred;
   this is not concealed as a single two-submission execution.
3. **Light device-name coverage was low.** Only one of eleven devices had a reported
   name, from mDNS; Deep obtained this PC's name by reverse DNS. Lack of a name does
   not imply an intruder. The fresh folder had no previous aliases/history, and
   advertisement availability is not guaranteed. This run does not prove a naming
   regression. Record individual lookup failure/source reasons and evaluate a
   bounded name refresh and router-client-list guidance before adding more probes.
4. **Novice wording can still improve.** The visible completion text says eleven
   devices were "identified during discovery", although ten had no reported name.
   "Found during discovery" would avoid implying a verified identity. The known
   self-computer still displays "Type not identified" alongside its known role.
   Some summaries repeat both a friendly feature name and protocol/port notation;
   source/confidence qualifications can overwhelm the first practical instruction.
   These are presentation findings, not missing scan evidence.
5. **Date-filter mismatch reproduced with the actual reports.** Both successful
   scans display `14/10/2026` in the browser, but their preserved creation timestamps
   are on 13 October UTC. Searching the isolated store for 14 October UTC returned
   zero reports; 13 October UTC returned both. The filter's UTC label is technically
   correct, but the report header does not identify its local display zone. Align
   or clearly explain those conventions so a novice can find the date they see.

No additional scanner/parser/rule/validated-AI corruption was found in the completed
pair. That is a scoped finding, not proof that no architecture or usability bugs
remain. The source-research findings below still need their stated reproductions.

## Recommended next work

Use the detailed [eleven-point research brief](ui-ux-recommendations-20261014.md)
for implementation and acceptance tests. The highest-value sequence is:

1. Reproduce and prevent keyboard focus loss when a running-job poll recreates its
   Open/Cancel controls; preserve stable, keyed action nodes.
2. Disambiguate repeated report titles in selection and deletion confirmation using
   scan type, recorded date/time and target summary. Preserve bounded selection,
   exact revision checks and the safe cancellation default.
3. Clarify browser-local displayed dates versus UTC date filters, including midnight
   and daylight-saving cases. Do not change original evidence timestamps.
4. Make settings-save feedback durable; provide deliberate recovery after leaving
   Saved reports and include recovery storage in disk accounting/backup guidance.
5. Refine the observed novice wording and role-aware first actions; make protocols,
   ports and confidence qualifications secondary while retaining accessible evidence.
6. Test custom scroll reveal with actual assistive technology and nontechnical
   participants before claiming it improves usability. Twenty-four rows and an
   empty initial view remain product choices, not standards requirements.

Light took about seven minutes including eleven device checks and eight AI records.
Stage timing deserves a measured optimisation study; a one-device Deep duration
is not an equal-work benchmark. Do not speed up the UI by hiding failed checks,
claiming incomplete work passed, or removing factual limitations.

## Offline verification

`scripts/check.py` passed in `.test-artifacts/checks-b773566204/`: 653 Python tests,
five actual Windows symlink-privilege skips, 91 deselections, all 190 JavaScript
tests, Ruff, 156-file formatting and eighteen shipped JS syntax checks. Scans and
providers were excluded from that gate; its results are separate from the live pair.
The new verification helpers also pass their focused Ruff checks. An initial
helper lint issue with `return` in cleanup and a replay-helper lambda lint issue
were corrected; neither changed production application code. The completed pair
and its evidence are preserved without executing the proposed UI/UX fixes.
