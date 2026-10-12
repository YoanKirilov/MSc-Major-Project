# Home live review and fixes — 8 October 2026

## Authorised execution plan

The user confirmed the newly detected home range `192.168.1.0/24` and this
Windows computer (`192.168.1.60`). Light checks that range; Deep checks only
this computer. Use an owned loopback backend and separate JSON storage. Do not
alter the existing server, saved settings or reports. Pi-hole remains deferred.

1. Run baseline Light and Deep through the browser. Keep raw XML, progress,
   coverage, AI records, and failure reasons in private test artifacts.
2. Investigate Windows connection-query timeouts with bounded read-only adapter
   measurements. Improve the query only if its required identity/routing facts
   remain intact. Never ignore a network change or use stale connection data.
3. Complete saved-date handling in report ordering/search and the recent-device
   picker. Keep readable evidence accessible even when its date is uncertain;
   exclude uncertain/future dates from recent device choices.
4. Make package verification use explicitly pinned build tools in an isolated
   environment, without installing tools into the normal app environment.
5. Run focused regression tests, the complete offline suites, browser workflows
   and a fresh packaged-installation check. Repeat authorised live checks after
   scanner changes; replay their raw XML/rules and validate AI output against
   the saved facts. Record incomplete coverage honestly.

## Baseline observation

Nmap 7.991 and local Ollama `llama3.2:3b` passed preflight. Light was submitted
as `fb7538db-df3c-476d-8f50-0b1a9e04bf7c`; starting Deep was rejected with
HTTP 409 because the connection could not be verified. The Light server log
also records `adapter_query_timeout`. The verification harness then stopped
its own backend; this is **not** a successful full Light/Deep baseline.

The normal backend was not stopped. Completed measurements, fixes, verification
counts and post-fix live results are recorded below.

## Implemented fixes and improvements

### Connection verification reliability

Replaced the expensive Windows aggregate query with one bounded, read-only
PowerShell process joining connected IPv4 interfaces, addresses, default routes
and network profiles. Cmdlet errors terminate the query rather than publishing
partial data. Typed validation rejects malformed/ambiguous output; interface,
address and gateway ordering is canonical so enumeration order alone is not a
network change.

Three aggregate measurements took **4.401 / 4.008 / 5.052 seconds**, versus
**1.244 / 1.348 / 1.789 seconds** for the initial direct-query candidate. The
final connected-interface-filtered implementation took **1.396 seconds** in
preflight and retained the home address, prefix, interface index, profile and
gateway. Absent gateways changed from `[null]` to `[]`; disconnected/loopback
enumeration differs, not the verified home connection. The query still has an
eight-second deadline. Overlapping reads share work; later reads are fresh.
Changed/unavailable connections and suspension still stop scanning. This is a
measured performance improvement, not a guarantee that Windows can never stall.

Primary command references: [Microsoft IPv4 addresses](https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-netipaddress),
[IP interfaces](https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-netipinterface),
and [the former aggregate query](https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-netipconfiguration).
No network settings, adapter selection or authorised range was changed to bypass
the guard.

### Saved-date consistency and understandable display

Nine new synthetic cases reproduced **seven failures** before the fixes.
Compact summaries now sort actual UTC instants before pagination. Search uses
the same aware-time parser as comparisons and nicknames. Unknown/naive/overflowing
dates remain accessible without date filters, with a warning; date filters use
UTC days. Recent-device choices reject unknown, old and future dates and select
the genuinely latest qualifying report. Original JSON/date strings are unchanged.

A shared display helper now uses “Date unavailable” / “Time unavailable” for
uncertain metadata in history, device choices, activity and identification
details. It rejects invalid calendar days and rollover times rather than allowing
JavaScript to silently turn them into another day. The existing layout is unchanged.

### Repeatable package verification

Added `requirements-build.lock`, included by the development lock. The package
check provisions pinned build tools in its own environment and builds with
`--no-isolation`, then tests a separately installed wheel with Python `-I`.
`--offline --wheelhouse <directory>` disables package-index access; missing/invalid
cache options fail before installations begin. Build tools were not installed into
the normal runtime or existing quality environments.

The private Windows/Python 3.14 wheel cache was prepared from the package index
using the existing runtime/test pins and explicit build pins. The subsequent build,
install and package checks used **only that local cache**. This does not establish
byte-for-byte reproducible wheels or provide a cache for other OS/Python versions.

### Dependency-audit coverage gap

Inspection of the first audit JSON revealed that `pip-audit --disable-pip` had
checked only **11 top-level development pins**, ignoring `-r` includes. That pass
did not cover the runtime or newly included build/client pins.

`scripts/check_security.py` now recursively flattens each lock graph into a
private audit input, rejecting out-of-project includes, unpinned entries and
conflicting versions **within an environment**. Development/runtime/build/client
and security tooling are validated and audited **separately**; their intentional
different `filelock`/`platformdirs` versions are not treated as one installation.
Returned audit JSON must cover every platform-applicable input package/version;
missing or skipped packages fail the gate. No packages were auto-updated or ignored.

The corrected audit covers **43 development/runtime/build/client pairs** and
**32 security-tool pairs**, with no known vulnerabilities in either output.
Focused flattening/coverage/gate checks passed **13 cases**. Failed intermediate
diagnostics are retained; they are not reported as successful security gates.

## Post-fix actual home results

Artifacts: `.test-artifacts/home-review-20261008-postfix/`. Scans ran concurrently
through a separate authenticated loopback backend. Nmap **7.991**, Ollama
**llama3.2:3b**, prompt **4.2.2**. These reports are in test JSON storage, **not**
the normal Saved reports list.

| Check | Light home range | Deep this Windows PC |
| --- | --- | --- |
| Report ID | `efa5b34a-d88a-45f6-bf97-d61d2a437f8c` | `ced6ae9d-85be-444b-a929-6dcd499a8b8a` |
| Observed elapsed time including AI | 805.1 seconds | 545.5 seconds |
| Selected/discovered device checks | 23 finished of 24 discovered | 1 finished of 1 selected |
| Responding services | 21 | 13 |
| Review items | 9: 1 medium, 4 low, 4 informational | 4 informational |
| AI records including overview | 10 ready | 5 ready |
| Unfinished checks | 1 unreachable device | None |

Light's `192.168.1.231` could not be reached on either bounded attempt
(2.390 / 2.181 seconds; Nmap exited normally but did not supply a completed
device check). It may be asleep, disconnected or not answering; its actual cause
is **unknown**. The report says **“Scan finished; 1 device could not be checked”**
and offers a separate retry. This is not relabelled as complete or treated as a
reproducible application defect. The 230 other silent discovery addresses were
not service-checked and are not counted as failed device checks.

There was no post-fix connection-query error. Deep finished enrichment and AI;
its self-routing note correctly warns that this does not establish access from
another device or the internet. Light did not discover the scan computer, and
the saved-ledger notice says so; the separate Deep report is not silently merged
into Light coverage.

Light saved seven mDNS announcements and **19 current names**, all selected from
reverse DNS; four completed device results remain unnamed. Deep recorded one
reverse-DNS name. These are reported clues, not verified identities or Pi-hole
results. One Light service qualified for an exact-version CVE reference lookup;
no Deep service did. No real NVD lookup ran and no CVE was guessed from a port.

## Evidence, AI and beginner-facing review

Read-only raw-XML replay matched **345 Light / 20 Deep** typed service records,
including non-open/unknown states, and all **13 deterministic review items**.
These record totals are not counts of open ports or proof of full security coverage.
All **15 accepted Ollama records** revalidated against their saved facts and
reviewed alternatives; **zero rejected fields or fallback records** in this pair.
Model inputs contained no observed IP/MAC/hostname or raw XML. Evidence, severity,
selected checks and incomplete coverage were not changed by AI.

Report text and mobile screenshots were reviewed from a beginner's perspective:
the first action names the device to recognise, ordinary words explain sharing/web
pages, priorities are not a security score, missing names do not imply intruders,
and self-check/incomplete limitations are visible. Original wording and technical
evidence remain expandable. This is a developer review, **not** a reader-study score.

The live browser check passed refresh/resume without duplicate submissions, history
search/reopening, Light Run again and Deep's same-device choice. Both reports passed
320/390/768/1440-pixel widths with no horizontal overflow or page errors. Exactly
two post-fix scan submissions were made. All copied historical reports and pre-existing
normal report files passed hash checks. The owned backend stopped and port 8766 was
free afterwards; the normal backend remained available on 8765.

## Regression and installation verification

- Focused connection/guard/remediation checks: **60 passed**.
- Focused dates/library/storage/history checks after repair: **82 passed**.
- Pinned-build option/dependency-lock checks: **4 passed**.
- Broader regression: **590 Python tests passed**, one live-provider test deselected,
  including Chromium/Firefox/WebKit synthetic workflows and eight responsive sizes;
  **74 JavaScript tests**, lint/format and all **11 module syntax checks** passed.
  Artifacts: `.test-artifacts/checks-8324a57492/`.
- Final complete gate after the calendar validation and new browser assertions:
  **590 Python / 74 JavaScript tests passed**, one live-provider test deselected;
  all three browser engines, lint/format and 11 syntax checks passed again.
  Artifacts: `.test-artifacts/checks-9883c07dd8/`.
- Post-display-update offline gate: **574 Python / 74 JavaScript tests passed**,
  nine opt-in tests deselected; lint/format passed for **140 files** and all syntax
  checks passed. Artifacts: `.test-artifacts/checks-c318713058/`.
- Final post-audit-fix offline gate: **582 Python / 74 JavaScript tests passed**,
  nine opt-in tests deselected; lint/format passed for **141 files** and all 11
  syntax checks passed. Artifacts: `.test-artifacts/checks-3f4bc7cf88/`.
  Application/browser source is unchanged from the complete three-engine gate;
  the eight additional Python cases test the audit tooling, not scanning.
- Added uncertain-date history browser assertions separately passed in Chromium,
  including retained report bytes and date-filter exclusion:
  `.test-artifacts/library-browser-final-20261008/`.
- Fresh offline installed-wheel check passed six rendered pages, **12 assets** and
  demo creation/reopening, with no broken requirements. The first pinned build and
  the post-display-update build both passed; their artifacts are
  `.test-artifacts/package-cce4fb79fd/` and `.test-artifacts/package-9617bee5e3/`.
  A final freshly built/installed wheel containing the calendar validation and
  updated README passed again: `.test-artifacts/package-b998a414e4/`.
- Corrected complete dependency/advisory audits found **no known vulnerabilities**
  for the 43/32 checked environment pairs;
  Bandit recorded **15 low / zero medium-high** findings, and the offline secret gate
  found **zero potential secrets**. These are bounded tool results, not security
  certification. Final artifacts: `.test-artifacts/security-850dda65ee/`.
  The earlier `.test-artifacts/security-c308b46746/` had incomplete dependency
  coverage and is superseded by this corrected result.
- All **67 application Python modules**, five templates and 12 assets remain
  referenced/reachable. No unused source file was proven safe to delete. Private
  artifacts, environments, user edits and earlier dated evidence were preserved.

The final calendar-rollover tightening passed focused JavaScript cases and the
final complete gate above; it does not alter scan execution, facts, layout or dates
stored on disk. A read-only check confirmed the normal saved network and interface
are already automatic (both unset), with no scope override in the current shell.

## Remaining recommendations and honest limits

1. Retry the unreachable device only when its owner confirms it is awake and
   connected. Do not increase severity, declare it absent or weaken the guard.
2. Evaluate the long mobile report and repeated informational items with actual
   nontechnical readers before another layout rewrite. Physical phones, screen
   readers and the authorised Ubuntu lab still need separate evaluation.
3. Consider controlled long-running/concurrent adapter-read measurements and
   identifier-free duration logging. Do not introduce stale identity caching.
   One successful pair cannot eliminate every possible Windows timeout.
4. Add per-platform checked wheel caches and hashes if stronger supply-chain/offline
   repeatability is required. The existing checked cache covers this machine only.
5. The previously intermittent Windows socket-shutdown reset did not recur here;
   it remains an unreproduced runtime follow-up. Pi-hole deployment and live NVD
   provider validation remain deferred. No participant results were fabricated.

Restart the normal backend when idle to load backend changes; do not interrupt an
existing user scan. Refresh open pages for the display updates. There is no SQLite
or framework migration, no exploit/password attempt and no packet capture.
