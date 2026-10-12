# Repeat live scan and architecture review - 7 October 2026

This is a review, not an implementation pass. Application code, normal reports and
real nicknames were not changed. The findings below describe the pre-fix version.
Implementation followed in [the 7 October execution record](development-plan-20261007.md);
use that record for current fix and verification status.
The previous four application fixes are still in place; this review adds evidence
for previously uncovered nickname failure paths and reconfirms the dashboard issues.

## Live scope and outcome

WiFi was reverified as 192.168.0.216/24, gateway 192.168.0.1. The normal app on port
8765 remained available. Its public pages and all eleven CSS/JavaScript assets
matched current source and used no-store caching; its private API required a session.
The user's existing session was not extracted or bypassed.

Exactly two fresh jobs were submitted through a browser to an owned instance of
the same code on 8766, using separate JSON data and copies of earlier test reports.
This verifies a fresh instance, not authenticated scanning through the existing
8765 session. Light covered the authorised home /24; Deep targeted this Windows
computer only. Nmap 7.991, automatic scope, mDNS readiness, local Ollama llama3.2:3b
and JSON storage passed preflight. No Pi-hole or online CVE-provider request was made.

| Measurement | Light | Deep - this PC |
| --- | ---: | ---: |
| Scan ID | 0e39c943-ce38-46fd-8d10-abd92d83175a | a6a10b1d-38be-4180-b5a3-c6f93818ed2f |
| Elapsed, including report preparation | 295.1 seconds | 542.4 seconds |
| Device checks finished | 8 of 8 discovered | 1 of 1 selected |
| Open services | 10 | 13 |
| Review items | 7: three low, four informational | 4 informational |
| Scanner errors / unfinished selected checks | 0 / 0 | 0 / 0 |
| Accepted AI records, including overview | 8 | 5 |

The preceding Light run discovered twelve addresses and could not check one of
them. This run discovered eight. In particular, 192.168.0.154 was not discovered;
it was not successfully retested. A smaller discovery count is not proof that a
device was removed, fixed or compromised. Completed means the selected/discovered
checks finished, not that all devices or all possible security problems were found.
Deep retained its self-routing warning: responses here do not prove that other
devices or the internet can reach the same services.

## Verification and architectural assessment

- XML replay matched all 120 Light / 20 Deep service-state records and all seven /
  four deterministic findings. All thirteen accepted AI records revalidated against
  reviewed source-bound alternatives, with zero rejected fields or fallback records.
  Reconstructed selected AI inputs contained no IP, MAC, hostname or raw XML.
- Real reports passed refresh recovery, history search/reopening, Run again setup
  and no horizontal overflow at 320/390/768/1440 px. Exactly two scan submissions
  were recorded; the additional read-only inspection submitted none.
- Fresh regression passed 459 Python and 61 JavaScript tests, Ruff lint/format,
  ten module syntax checks and three-browser responsive tests across eight sizes.
  One opt-in live-provider fixture was deselected; Ollama ran on the actual reports.
  Regression artifacts: `.test-artifacts/checks-a74aecd9a7/`.
- No live-backend exception traceback, HTTP 500, browser page error or recorded
  asyncio lifecycle diagnostic occurred. The synthetic fault probes below did
  produce HTTP 500s; these are separate from successful live-scan outcomes.
- All 65 application Python modules remained import-reachable. Public/routed assets
  and the regression suite remain in use. No unused application file was established
  by this review, and no source file was deleted. Static reachability is not proof
  that every branch is exercised.
- Existing normal and copied historical report files, including XML, were unchanged
  by byte hashes. The owned backend was stopped and port 8766 confirmed closed;
  normal port 8765 continued serving the app.

The architecture remains suitable for a local, single-user research prototype:
one backend owns one JSON folder; five unique admitted jobs share two scanner slots
and a serial AI slot; queue/execution budgets, guarded network snapshots, typed
parsing, deterministic findings and separate annotations are retained. The workflow
still saves facts before Ollama and waits for validated preparation before reporting
readiness. JSON does not need replacing with a database to fix the findings below.
This is not a certification or a claim of multi-user production hardening.

## Findings, in recommended execution order

### 1. Confirmed bug: nickname failures return generic HTTP 500

Sources: `app/api/scans.py:set_nickname`, `app/api/library.py:nicknames` and
`app/storage/nicknames.py`. Other report-note routes use `note_operation`, but
nickname reads/writes do not have an equivalent complete failure boundary.

An isolated TestClient probe with synthetic reports reproduced:

- Disk-full OSError during nickname PUT: HTTP 500, "Internal Server Error".
- Nickname read OSError: snapshot GET returns 500.
- Invalid nickname JSON: snapshot GET also returns 500.
- In both read cases the full factual report still returns 200 with nickname_error.
  Existing nickname bytes and original scan evidence were preserved on failed PUT.

Fix later: give nickname routes consistent readable unavailable/conflict responses;
retain 404 for a genuinely missing report/device, revision conflicts, authentication
and CSRF. Do not automatically replay writes or reset names after a failed read.
Add focused fault tests before changing the boundary. A passing general suite did
not cover these specific cases; these new probes are diagnostic findings, not fixes.

### 2. Reliability gap: nickname backup exists but is not used for recovery

`NicknameStore._update` saves nicknames.previous.json, but `_load` reads only the
primary. The probe created two successful synthetic edits, then corrupted only the
synthetic primary. The backup validated at revision 2, but snapshot GET returned
500 and report names were unavailable. Both the backup and scan evidence remained
intact; no permanent loss of those files was demonstrated.

Fix later: recover a validated previous copy under the nickname lock, quarantine
bounded corrupt primary bytes, advance revision beyond stale editors, and display
that recent nickname edits may be missing. Cover simultaneous readers/writers,
stale revisions, invalid backups, oversized files and unsafe paths. Never silently
reset the global nickname document or extend an old identity anchor's age.

Evidence for findings 1-2:
`.test-artifacts/repeat-review-20261007/nickname-failure-probe.json` and
`probe_nicknames.py`. Fault data is isolated in nickname-fault-data; no real nickname
file was corrupted, edited or recovered by the probe.

### 3. Confirmed existing UI issues: Deep refresh misrepresents setup

Sources: `app/static/js/dashboard.js:resumeScan` and `app/templates/dashboard.html`.
At 390 x 844, the resumed progress panel started at y=1361.125, outside the initial
viewport. Setup stayed above it. The Deep host input was blank and editable, although
the backend retained the correct immutable target 192.168.0.216 and the launch
button was disabled. Progress itself was not lost and the job was not retargeted.

Fix later: populate a read-only active target from saved job metadata and disable or
collapse irrelevant setup controls. Promote progress on initial launch/reconnection,
without repeatedly scrolling or stealing focus during polls. Preserve the existing
visual style. Test in-viewport progress, the restored target and disabled setup
controls, rather than only DOM visibility/no-overflow. Cover pinned links, blocked
browser storage and independent Light/Deep tabs.

Evidence: clarity-and-progress-browser.json and before/after-scroll screenshots in
the fresh artifact folder. This reconfirms the preceding review, not a new regression.

### 4. Input-hardening recommendation: explicitly cap known-host requests

`ScanCreateRequest.hosts` has no list-length bound, and the pure scope validator
does not cap known-host count independently of scope. A network-free probe accepted
300 distinct synthetic private addresses through the schema and helper with a
synthetic /16 allowed range; discovery of a /23 was correctly rejected.

Important limit: normal Settings validation only permits /24 or smaller ranges.
The 300-address case is a helper/server-configuration hardening case, not a live
request reproduced through the normal home UI. No 300-host scan was run. Public
addresses were still rejected. Large raw lists can nevertheless be presented to
the schema before duplicate/scope checks.

Improve later: define and test one explicit Light known-host cap, bound address
strings and enforce the same policy in schema and core validation. Review server
environment scopes for consistency with Settings; keep Deep's one-host rule. Test
the limit and limit+1 without network calls. Consider a separate bounded request-body
policy if the app's exposure expands. Evidence: target-boundary-probe.json.

### 5. Known unresolved runtime issue: intermittent Windows socket reset

It did not recur in either new live job. That is not proof of a fix. Retain sanitized
diagnostics and a bounded reproduction/compatibility check before choosing a runtime
remedy; do not hide the error or make an unsupported global event-loop change.

## Experience and scanning improvements

1. **Explain absent devices separately from unfinished checks.** Offer a cautious
   "seen earlier, not observed now" view based on recorded previous observations.
   Do not count every silent address as a failed selected check or imply an absent
   device is fixed. The current comparison summary covers displayed devices only.
2. **Make remaining raw feature labels more useful.** Use reviewed descriptions for
   probed products such as the remaining vmware-auth labels. Keep original names,
   protocol/ports and confidence in technical details. Never rename an unconfirmed
   feature or choose a CVE solely from a port number.
3. **Shorten repeated first-action text.** Keep permission/recognition cautions, but
   avoid making a user identify this scan computer through the router as if it were
   an unrelated device. Keep gateway explanations available without repeating the
   long role definition in every checklist label.
4. **Make naming coverage understandable.** No current mDNS announcements were
   captured in this short run. The Sony name was correctly marked previously
   reported; Deep used reverse DNS. A missing name is not evidence that a device is
   suspicious. Show current versus historical sources and offer bounded rechecking
   when a device is awake; do not infer identities from address reuse.
5. **Validate comprehension with real readers.** Ask a nontechnical participant to
   explain open services, identify the first safe action, distinguish Checked from
   a verified repair, and locate incomplete coverage. Automated wording and browser
   checks do not establish comprehension or physical-phone accessibility.

Pi-hole remains deferred. Four Light services met the versioned CPE lookup gate;
none did in Deep. That is lookup eligibility, not a confirmed vulnerability. A real
online CVE-provider check, physical-phone/assistive-technology evaluation and an
authorised Ubuntu lab run remain outside this verification. Package installation
and dependency/security gates were not rerun here; their earlier evidence is not
being represented as a new run.

Private live artifacts: `.test-artifacts/repeat-review-20261007/`, including IDs,
reports, XML, timelines, evidence-audit.json, browser-results.json,
source-and-frontend.json, integrity.json, cleanup.json and both synthetic probes.
Do not publish backend logs: they include the owned test session bootstrap URL.
