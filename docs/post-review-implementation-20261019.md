# Post-review implementation - 19 October 2026

Implements the authorised follow-up to the
[18 October live review](live-review-post-improvements-20261018.md).
The audit remains a historical record of the defects observed before these fixes.
Keep FastAPI, authoritative local JSON, existing scan scope protections and the
simple interface. No SQLite, Pi-hole deployment, dependency upgrade or publication.

## Execution order and completed changes

1. **F1: targeted retry eligibility.** The document now owns one explicit policy,
   projected to the browser and reused by the retry endpoint. A selected/observed
   target skipped specifically because its queue expired is eligible. Completed
   checks, deliberately excluded targets and silent discovery addresses stay out.
   The legacy browser fallback uses the same reason-qualified rule. Revision,
   authorisation, current scope/profile and admission checks remain mandatory.
   Retry creates a linked report; it does not rewrite the original evidence.
2. **F2: unknown CVE applicability.** Product mapping is now tri-state: related,
   usable nonmatching, or unknown. Missing/null/empty/malformed mapping nodes and
   exhausted traversal budgets stay unknown instead of becoming "no matches".
   Negated criteria cannot create a positive match. The new `product-research-3`
   policy invalidates older cached research. Port coincidences are not CVE matches;
   neither related references nor no results establish a device's safety.
3. **F3: isolated name resolution.** Reverse DNS now uses at most two owned,
   isolated standard-library Python helpers, not the default JSON I/O executor.
   Admission, execution, captured output and process cleanup are bounded; cancelled
   work is joined and capacity released. Only validated private IPv4 addresses are
   accepted. No shell, user-controlled executable or raw error text is used.
4. **Naming diagnostics.** Original reverse-DNS checks and explicit later name
   refreshes retain source/status/elapsed-time diagnostics. Optional device details
   distinguish a returned name, no answer, timeout, busy or failed source; mDNS
   refreshes distinguish not-checked as well. No late name becomes a verified
   identity, new reachability evidence or a scan finding. Old JSON remains readable.
5. **Cross-tab CVE completion.** Each service keeps its last eight completion
   receipts under the existing annotation lock. GET-only lost-response recovery can
   recognise an earlier tab's receipt after another cached lookup. Research dates
   and references are not relabelled as new research. Receipt-only changes do not
   rebuild open disclosures. Attempts older than the bounded history can still be
   unconfirmed; the app never silently repeats their POST.
6. **Process freshness.** A frozen app-source build ID, API contract and start time
   are exposed in status/Settings and response headers. A cached source comparison
   detects files changed since process import. Client/backend mismatch produces one
   non-focus-stealing restart notice and blocks only contract-dependent CVE writes;
   saved-report reads and cancellation remain available. Static freshness alone is
   no longer treated as a backend restart. The live helper checks this contract too.
7. **Measured rich-history load.** `scripts/benchmark_library.py --rich` adds rich
   synthetic histories, concurrent inventory/search/checkpoint writes, joined
   synthetic cancellation and source-hash preservation. Existing lightweight mode
   remains available. Every run creates a new private folder and never invokes
   Nmap, DNS, NVD or a model. See measurement limits below.
8. **Reader/assistive-technology protocol.** New prepared tasks in
   [evaluation-session.md](evaluation-session.md) cover uncertain names, targeted
   retry, CVE unknown coverage, version notices and cross-tab recovery. Actual
   consented participants, spoken screen-reader output, true zoom and physical
   phones remain pending; automated checks do not complete that recommendation.

The resolver reuses the bounded scanner subprocess runner. A separate Windows
sleep-helper probe also checked the owned PID was absent after its timeout; it did
not contact a device. CPython's [Windows venv launcher source](https://github.com/python/cpython/blob/3.14/PC/venvlauncher.c)
documents its redirection and owned process-job handling. This local observation is
not a guarantee about every Python distribution or arbitrary descendant processes.

## Verification

- Full offline gate `.test-artifacts/checks-e72c3e36da/`: **957 Python passed**,
  five Windows link-privilege skips, 152 opt-in cases deselected; **274 JavaScript**,
  29 syntax checks, lint and 197-file formatting passed. The earlier interim gate
  passed 956 Python/274 JavaScript before the additional rich-history case.
- New focused Python file has **19 cases** covering retry selection/revision/CSRF,
  unchanged original evidence, tri-state/bounded CVE traversal, resolver isolation,
  private-address validation/admission/cancellation, frozen build reporting, bounded
  receipt history and rich concurrent storage. Provider/scanner calls are synthetic.
- Actual Chromium/Firefox: **16 passed**, zero failures/errors/skips, in
  `.test-artifacts/post-review-browser-20261019/`. Includes old-contract warning and
  readable reports, CVE writes prevented before submission, actual response policy,
  mobile Settings build details, lost CVE reply/cache recovery and device library.
  This is a focused pair of engines, not a new full hosted platform/browser matrix.
  The eight CVE cases then passed again in
  `.test-artifacts/post-review-cross-tab-browser-20261019/` after extending lost-reply
  fixtures to send an explicit second cached request before the first tab recovers.
  That rerun strengthens eight of the original cases; it is not 24 distinct cases.
- Installed-wheel check `.test-artifacts/package-e167582582/` passed using only
  local pinned wheels: seven pages, 31 static assets, synthetic report/demo creation,
  reopening and delete/Undo; installed dependencies are consistent.
- Security `.test-artifacts/security-67a2d467aa/` passed: no known vulnerabilities
  in either audited dependency graph, zero medium/high static alerts, zero potential
  secrets. All 16 low static alerts remain recorded, not suppressed.
- Fresh authorised live pair `.test-artifacts/post-review-live-20261019/` passed
  through a separate current-source backend and new JSON folder. Its frozen source
  build was `3e5d3881e53f804e688b`, API contract 2, with matching source at preflight.
  Final results, browser/evidence checks and cleanup follow below.

### Fresh live results

The confirmed default-route range and this-PC address exactly matched the previous
home authorisation before either scan started. Only that range and this PC were
scanned. Pi-hole remained disabled; existing nicknames/history were not imported
into the isolated test dataset. The normal server was left running.

| Result | Light network | Deep, this PC |
| --- | ---: | ---: |
| Device checks finished | 6 of 6 discovered | 1 of 1 selected |
| Unfinished device checks / recorded check errors | 0 / 0 | 0 / 0 |
| Open features | 10 | 14 |
| Review items | 7: three low, four informational | 4 informational |
| Duration including explanation processing | 261.1 s | 538.2 s |
| Ready explanation records, including overview | 8 | 5 |
| Fixed-wording fallback records / rejected fields | 0 / 0 | 0 / 0 |
| Names recorded | 0 | 1, reverse DNS |

Deep retained the expected `SELF_SCAN_LOCAL_ROUTING` warning: local answers do not
establish access from another device or the internet. It is not a device-check
error. Fourteen local answers, rather than the earlier thirteen, are observations
at this check time, not proof of new exposure or an intruder.

Light's six reverse-DNS checks timed out at at most 2,018 ms; zero mDNS observations
were returned in this run. Deep's reverse-DNS source returned a name in 148 ms.
This demonstrates working source diagnostics and bounded helpers, not a promise
of more names or an established cause for the changed discovery count. This PC
was not a Light result; do not claim its Deep name was lost for a matching entry.
Other silent/offline devices may exist. No name-refresh probe was added to this
live verification, and no nickname was invented or overwritten.

- Exactly two browser scan submissions; refresh retained both jobs without a
  duplicate POST. Both reports opened automatically after explanation processing.
- Zero browser page errors or page overflow at 320/390/768/1440 px for both reports.
  Private export previews, inventory filtering/reset and exact return context
  passed. The isolated inventory contained seven saved observations, not a count
  of all currently connected physical devices. These viewport checks are not a
  physical-phone/true-zoom or real-AT evaluation.
- XML replay reproduced **111 service records**, **11 deterministic findings**,
  host script evidence and one saved certificate-date interpretation, with no
  missing raw host evidence. All **13 ready explanation records** revalidated;
  selected model inputs contained no recorded IP/MAC, hostname or raw XML.
  Ready does not mean every sentence was rewritten: the model may retain reviewed
  original wording. This replay is consistency verification, not an independent
  lab measurement of detection accuracy.
- All **853** protected existing normal report/evidence files stayed unchanged.
  The owned backend stopped after both jobs finished; an independent read-only
  check found its port closed and both recorded parent/child processes absent.
  Normal server process/session ownership was not changed. Backend log inspection
  found no recorded ERROR/traceback/unretrieved-task exception.

The visible report overview explains "features" with web-page/file-sharing examples;
counts and coverage remain factual. First actions preserve HTTP/certificate
precautions, and the Windows self-check advice explicitly says not to disable the
firewall or core services. "Network gateway (recorded route...)" remains dense;
the prepared novice tasks should measure this before more wording/control changes.
This assistant walkthrough is not evidence that every reader understands it.

### Rich-history measurements

Each rich report contains 16 synthetic devices and 128 feature records, including
bounded script text. Six hundred source JSON files occupy about 79.7 MB combined;
each individual report remains well below the storage file limit. Warm search may
still read 88 full files above the 512-entry cache; it is not a permanent index.
Inventory retains its 200-candidate and 24-links-per-device limits with explicit
warnings. This benchmark must not be described as an unlimited complete inventory.

Final measured run: `.test-artifacts/library-bench-9d2b1a517d/`.

| Measurement | 32 reports | 600 reports |
| --- | ---: | ---: |
| Cold search / full JSON reads | 0.248 s / 32 | 5.701 s / 600 |
| Warm search / full JSON reads | 0.085 s / 0 | 2.268 s / 88 |
| Mixed-load search | 0.171 s | 2.499 s |
| Mixed-load inventory | 0.394 s | 4.061 s |
| Checkpoint saves, including saves completed while reads were pending | 3 / 2 | 3 / 2 |
| Synthetic cancellation plus terminal save | 0.034 s | 0.031 s |

Both terminal cancellations saved correctly, admission slots were released and all
original benchmark report hashes stayed unchanged. Earlier benchmark iterations
did not guarantee overlapping saves; this run explicitly measures the overlap.
Timing is a local sample under other verification work, not a service-level
objective. The fake worker uses real
JSON/checkpoint/admission code, but not a live Nmap process. Its cancellation time
does not establish a live-scanner cancellation deadline or independent detection
accuracy. Report hashes verify preservation of the original benchmark evidence.

## Deployment and remaining evaluation

The normal server now exposes the earlier CVE operation request schema, unlike the
18 October audit. It still lacks the new build/contract headers, so it has **not**
loaded all changes in this record. It is not stopped by the isolated live helper.
Finish active work, restart **NetGuard: Start backend**, then reload the session
link printed by that task. Do not hard-stop an unrelated app process or infer a
successful deployment from the isolated test server.

No commit, push, hosted CI run or OS security change was made. Publish and verify
the retained platform/browser matrix only when the user explicitly authorises it.
Real novice/disabled-reader/AT sessions and independent Ubuntu/reference-lab
evaluation remain work requiring people/environment access, not fabricated passes.
Private session logs, raw XML, identifiers, screenshots and report text stay excluded
from ordinary uploads and documentation attachments.
