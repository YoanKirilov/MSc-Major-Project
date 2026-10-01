# Live verification - 30 September 2026

## Follow-up after the backend restart

The restarted server on port 8765 now advertises `/api/reports`, `/api/running-scans`
and `/api/recent-devices`. Its served dashboard, report and setup-helper JavaScript
matched the workspace files. Light, Deep and history pages returned HTTP 200; protected
APIs correctly returned HTTP 401 without a session. Runtime `pip check` passed.
The old-route deployment discrepancy described below is therefore resolved.

The existing server's current session token was not available to the checker: the
launcher prints it to its terminal rather than saving it in the data folder. No
authentication bypass, credential change or server restart was performed. The repeat
live scan used a fresh isolated instance of the same current code. This distinguishes
the verified deployment/routes from the authenticated end-to-end workflow tested in
isolation; the new result is not in the normal server's Saved reports.

### Repeat live outcome

Report `0bb69f02-3d34-4944-a3a5-3cbb4b6c7a1e` finished in **217.5 seconds**:

- Nine devices discovered, eight checked successfully; one address could not be
  reached for the service scan after two attempts. Nmap's retained output reports
  zero hosts up for that single-host check, not an installation/configuration error.
- Eleven open services and seven review items: three low priority, four informational.
- The scan correctly remains `partial`. The displayed headline is
  "Scan finished; 1 device could not be checked." The failed device has a separate
  visible card and retry guidance; it is not silently removed or declared safe.
- Ollama completed eight validated explanation records in two requests, with no
  rejected fields or fallback records. The overview preserves incomplete coverage.
- All 120 stored service-state entries and all seven findings matched retained-evidence
  replay. All eight explanation records stayed within approved source-bound choices;
  rebuilt model inputs contained no observed device identifiers or raw XML.
- Progress refresh submitted no duplicate scan. Actual report reflow checks at 390,
  768 and 1440 pixels passed. Reopened browser checks passed for all nine cards,
  searching the failed device, all seven finding panels, history, comparison display,
  and Deep picker prefill. The follow-up made zero scan-creation requests and reported
  zero browser script errors.
- Naming remained limited: one fresh reverse-DNS name, one historical name, six unnamed
  successfully checked devices and the unnamed failed device. A bounded TV name retry
  found no new name. No fresh mDNS name or Pi-hole operation is established by this run.
- All 41 original saved reports validated, and normal JSON hashes were unchanged.

The report is cautious and understandable in its main overview. The mobile screenshot
does reveal a remaining layout issue: the "Scan notes and unfinished checks" label is
squeezed into a narrow column, splitting words awkwardly. The shared `.simulation-note`
flex layout should stack that heading above the notes on narrow screens. The earlier
comparison-card identification, name-retry feedback and search-label recommendations
also remain. No application source was changed during verification.

### Verification interruptions retained

The first repeat attempt, `7c935667-92e8-4b31-954c-601b6e8f60f3`, encountered a local
progress-read "socket hang up". The checker then shut down its isolated server, leaving
that report honestly cancelled after seven of eight device checks, before AI preparation.
The precise transport cause was not established. The checker now retries only progress
GETs a bounded number of times; it never resubmits a scan POST. The application's own
dashboard already reconnects transient progress failures without forgetting the job.

The next scan reached its finished partial report, but the initial checker assertion
expected only eight successful-device cards. The app correctly rendered nine, including
the failed-device placeholder. Corrected the checker expectation and passed a follow-up
review of the same saved report; no extra port scan was needed. Neither interrupted
checker invocation is represented as an all-green live verification command.

Artifacts: `.test-artifacts/live-acceptance-20260930-b/` (interrupted attempt) and
`.test-artifacts/live-acceptance-20260930-c/` (finished report, evidence audit and passed
follow-up review). They contain private local network data and are ignored by Git.

The full three-browser regression rerun passed **328 Python and 43 JavaScript tests**,
lint/format and eight JavaScript syntax checks: `.test-artifacts/checks-7d49eacdee/`.
The live-provider unit test was deselected; real Ollama was exercised above. The existing
Starlette/httpx deprecation warning remains. Security gates passed: no known dependency
advisories, zero medium/high findings, 12 retained reviewed low findings and zero potential
secrets. Artifacts: `.test-artifacts/security-d9c34a31cd/`.
Deep scanning, Pi-hole, physical-device testing and reader evaluation remain unverified.

## Earlier run: outcome

One authorised home **Light** scan completed through the current browser/API workflow
in **192.4 seconds**. Nmap 7.991 checked all seven discovered devices successfully:
11 open services, seven review items (three low priority, four informational), no
failed host checks, no saved warnings/errors. This covers the Light profile's selected
12 TCP and three UDP ports, not every device or security condition on the network.
The remaining 247 candidate addresses were not observed during discovery, not proved empty.

Local Ollama `llama3.2:3b`, prompt version `4.2.1`, processed the overview and seven
findings in two requests. All eight records were ready, source-bound and without rejected
fields. Original evidence, severity and actions remained unchanged. Ollama selects
reviewed alternatives; the interface also prefers reviewed editorial wording. This is
not evidence that every displayed sentence was newly written by AI or that AI alone
improved comprehension.

## Isolation and running-app discrepancy

The detected Wi-Fi range matched the saved authorised home scope. The live check used
the current workspace code, an ephemeral loopback port and an isolated data folder.
Settings, nicknames and three recent reports were copied for realistic history checks.
All **41 normal saved reports** validated before the run, and hashes of the normal JSON
files matched afterward. The existing server and its reports were not modified.

The server already running on port 8765 returned an OpenAPI schema **without `/api/reports`**.
It has not loaded the latest library API. Restart that backend when idle, then reopen
its new session link and hard-refresh. A browser refresh alone cannot load new Python
routes into an old process. The successful live run verifies the current code in the
test instance, not deployment of the latest backend into that existing process.

The new report is kept in the ignored test folder, not added to normal Saved reports.
No router/DNS settings were changed; no second normal-data writer was introduced.

## Evidence and browser checks

- All 105 saved service-state entries matched replay of the retained per-host XML.
  All seven findings matched deterministic rule replay. This is an internal consistency
  check using the application's parser/rules, not independent network ground truth.
- All eight stored explanation records contained only their source-bound approved
  alternatives. Rebuilt allow-listed model inputs contained none of the observed
  device IPs, MACs, hostnames or raw Nmap XML. This was a payload-construction audit,
  not a network packet capture.
- Refresh during scanning retained the same job; only one scan-creation request occurred.
  The browser waited for analysis before opening the report, which also reopened after refresh.
- The actual report had no horizontal page overflow at 390, 768 and 1440 pixels.
  Viewport screenshots and all seven finding panels were reviewed. No browser script
  errors were observed. Physical-device/assistive-technology evaluation remains separate.
- Search selected a real device; history found the report by ID; an optional title saved
  separately; Deep setup offered the new Light observations without automatically scanning.
- A real reverse-DNS name retry saved a timestamped result without changing `scan.json`.
  A second bounded retry for the previously named TV saved no new name, retaining the
  old name as historical rather than inventing a new observation.
- The comparison panel opened and retained its cautious wording about address matching
  and previously open services not observed open now.

## Device names and Pi-hole

Only two of the seven device cards had names: one fresh reverse-DNS name and one reused
name from a previous report, originally obtained through mDNS. Five remained unnamed.
No fresh mDNS announcements/names were recorded in this scan or the TV name retry.
This does not establish a collector defect or that the other devices are absent;
successful discovery from a known-advertising device still needs a controlled live test.

Pi-hole was disabled and unconfigured. **Pi-hole authentication, lease import and name
extraction were not tested.** Nothing was installed or enabled for this run.

## Nontechnical-reader walkthrough and recommendations

The overview explains what a service is, distinguishes observations from a break-in,
shows the priority breakdown and gives a first action. Previously reported names are
explicitly labelled. These are reviewer observations, not a completed reader study.

Recommended next work, not implemented during this verification:

1. Detect frontend/backend version mismatches early and explain when a restart is needed.
2. Include an address or stable device label on comparison cards: five currently say
   only "Unnamed device", making their otherwise correct comparisons ambiguous.
3. Show name-retry outcomes immediately, such as "No new name found". Currently the
   result and uncertainty notes are inside a collapsed "Later identification lookup".
4. Rename "Search findings" to "Search devices and results" to match its expanded scope.
5. Reduce mobile repetition through optional collapsed technical material while retaining
   coverage and uncertainty. The real seven-device report is a long scrolling page.

No live Deep scan was launched: it needs a selected authorised device and a separate
evaluation. No five-job live load, Pi-hole deployment, Ubuntu run, physical-device audit,
large-archive benchmark or nontechnical-reader study is claimed.

## Reproducible evidence

Private ignored artifacts: `.test-artifacts/live-acceptance-20260930-a/`.
Report ID: `eb21f6c7-fd24-401d-948d-3562745fc9aa`.
The folder contains the live report/raw XML, timeline, preflight, verification JSON,
evidence audit, name-refresh records, panel text and screenshots. These include private
network details; do not publish the folder automatically. The run script refuses reuse
of its data folder and asserts the recorded home scope; review it before any later run.

Full regression rerun: **328 Python and 43 JavaScript tests passed**, Ruff lint/format
and eight JavaScript syntax checks. The three-browser responsive matrix covers 144
page/size/engine combinations, plus existing text/keyboard/touch checks. One separate
live-provider regression was deselected; real Ollama was exercised by the live run above.
The existing Starlette/httpx deprecation warning remains.
Artifacts: `.test-artifacts/checks-ed36d9a201/`.

Application code was not changed during verification. Only the verification record and
ignored local test harnesses/artifacts were added.
