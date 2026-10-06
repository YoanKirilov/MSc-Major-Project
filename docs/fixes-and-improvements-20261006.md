# Execution plan — 6 October 2026

Implement against the findings in `architecture-live-review-20261006.md`.
Preserve existing edits, normal reports, raw evidence and local JSON storage.

1. Centralise revision-aware report-note adoption. Synchronise every editable
   checklist, title, later-name and CVE panel in place, retaining focus, filters
   and expanded cards. Test older responses and cross-feature two-tab edits.
2. Map unavailable/corrupt notes and failed writes consistently without leaking
   filesystem details. Test failed reads/writes, recovery and evidence integrity.
3. Give each checklist control a device/address-specific, reviewed label.
4. Count unique active jobs across scans and saved-report AI retries; reject
   excess retries before changing the saved report. Test release/cancellation.
5. Explain Windows service labels, gateway/self-check limitations and review
   priorities. Provide specific conservative comparison-unavailability reasons.
6. Add explicitly user-owned checklist progress and filtering, separate from
   scan coverage and security. New reports start with fresh review status.
7. Benchmark cold/warm synthetic JSON history searches. Optimise only if measured
   evidence warrants it. Keep reader/phone/Ubuntu evaluation protocols actionable.
8. Remove the confirmed unused CSS rule; archive only generated folders using
   the scoped cleanup helper. Do not remove apparently unused framework callbacks.
9. Run Python/JavaScript checks, three browser engines and installed-package
   checks. Reverify the home interface, then run one Light and one Deep (this PC)
   in isolated storage through the browser. Replay saved evidence and AI validation.
10. Record exact results, remaining limitations and whether the normal running
    backend needs a restart to load these changes.

Not claimed complete by automation: actual nontechnical-reader comprehension,
physical-phone accessibility, authorised Ubuntu-lab evaluation, or the previously
intermittent Windows socket reset. No Pi-hole deployment or online CVE lookup is
part of these live scan tests.

## Implementation record

Steps 1–6 are implemented. `notes.mjs` now owns revision-aware note projection;
the renderer retains its DOM controls and visible state. Delayed older snapshots
are rejected even after a failed read. Name/CVE buttons regain keyboard focus after
temporary disablement; rejected delayed CVE replies cannot leave a busy label stuck.
All annotation API routes share the same readable error boundary. Unique admission
counts both job maps, while an admitted scan's automatic AI phase needs no new slot.
Storage and optimistic revisions remain authoritative; no write replay or scan
resubmission happens automatically.

The review's unused nested checklist-button CSS selector was removed. No unused
source module was identified or deleted. Generated build/cache output is archived
with the existing scoped helper; source, environments, reports and evidence stay.

### JSON search baseline

`scripts/benchmark_history.py` generated separate libraries with one synthetic
device per report and ran four identical searches. First-run versus median of three
warm searches: 100 reports 0.3121/0.2398 seconds; 500 reports 2.3848/1.4514 seconds;
1,000 reports 3.5740/2.8072 seconds. Cache stayed at its existing 512-entry limit
(about 345 KB of projections at 1,000 reports). Every expected report matched with
no unreadable-data warning. Cold means an empty process cache, not cold disk I/O.
Artifacts: `.test-artifacts/history-benchmark-cdf3b917ea/`.

This is a small synthetic baseline, not a percentile/load guarantee for large real
reports. No database migration or speculative index change was introduced. Above
512 reports, the bounded cache cannot retain every projection; revisit measured
search latency and cache working sets before adding more optimisation. Reader,
physical-phone and Ubuntu tasks are updated in `evaluation-session.md`, not marked
performed.

### Security gate review

The first gate identified one medium B104 alert on a `0.0.0.0` gateway comparison
in `config.py`. Inspection showed an absent-route filter, not a listener binding.
Only that exact line has a documented B104 exception; no global suppression or
runtime behaviour change was introduced. Rerun
`.test-artifacts/security-ec0b283cd7/` passed: no known dependency advisories, no
potential secrets, and 15 low static findings retained for review (zero medium/high).
This does not establish that the application has no vulnerabilities.

## Offline verification and organisation

Final command: `.venv-quality/Scripts/python.exe -B scripts/check.py --browser
--browser-engines chromium,firefox,webkit`. **459 Python / 61 JavaScript tests
passed**, one opt-in real-provider test deselected. Three engines, eight viewport
sizes, doubled text, lookup/checklist focus and next-step two-column grouping passed.
Lint/format and all ten module syntax checks passed. Artifacts:
`.test-artifacts/checks-f76f34ed60/`.

Fresh installed-wheel verification passed on the final template/CSS/module source:
six pages, eleven static assets, dependency consistency and demo create/reopen.
Artifacts: `.test-artifacts/package-5c39e0fc85/`. Earlier failed assertion runs were
not hidden: a focus issue was fixed, and a test expectation was corrected to count
both saved actions rather than only the first visible action. The full suite was
rerun after changes. A read-only audit reused only the source-traversal function
after rejecting a historical script's top-level fault-probe side effect; its guard
prevented modification of the prior evidence folder.

All 65 application Python modules remain import-reachable. Package/static-route
checks cover all five templates and ten JavaScript modules; callback/reference
candidates were not treated as deletion instructions. No source file was deleted.
`git diff --check` passed, apart from informational Windows line-ending warnings.

Cleanup removed `.ruff_cache/` and `build/` (94 files), after validated backup to
`.test-artifacts/cleanup-ab57686065bc4f3bb868980661dbdbd8.zip`. A final package build
regenerated `build/` (82 files), which was archived and removed again:
`.test-artifacts/cleanup-07906d0378c442c0a2a6339b611f2688.zip`.
The final cleanup preview lists zero disposable folders. Source, environments,
normal reports, historical evidence and IDE files were excluded. Removed generated
files are recoverable from these archives and can also be regenerated.

## Live verification

Reverified Windows WiFi `192.168.0.216/24`, gateway `192.168.0.1`. Nmap 7.991,
local Ollama `llama3.2:3b`, automatic scope and JSON storage passed preflight.
Exactly two jobs were submitted through the real browser to an owned loopback
backend on port 8766. Light covered the authorised `192.168.0.0/24`; Deep targeted
this Windows computer only. Previous isolated reports were copied for comparisons.
Pi-hole deployment and real online CVE lookups were not exercised.

| Measurement | Light | Deep — this PC |
| --- | ---: | ---: |
| Scan ID | `d294e951-5bd2-4460-a631-3d220ec1e416` | `f39fff5c-7a29-4eb9-91b4-915b69075c93` |
| Elapsed including queue/AI | 335.4 seconds | 602.1 seconds |
| Device checks finished | 12 of 12 discovered | 1 of 1 selected |
| Open services | 12 | 14 |
| Review items | 8: four low, four informational | 5: one low, four informational |
| Scan errors / unfinished device checks | 0 / 0 | 0 / 0 |
| Ready AI records, including overview | 9 | 6 |

Deep's one limitation note correctly explains local self-routing: another device
may see different services. The same caution is now prominent on the report page.
Deep recorded an HTTP response on TCP 2869 (`Microsoft HTTPAPI httpd`, detected
version 2.0), producing the additional low-priority review item. This is not proof
of a vulnerability or internet exposure. Different observed counts from earlier
runs are not proof of regression, repair or an intrusion; their causes were not
established.

Saved XML replay matched all **180 Light / 21 Deep** service-state records and
all **8 / 5** deterministic findings. All **15 AI records** revalidated against
reviewed alternatives with zero rejected fields or fallback records. Selected AI
inputs contained no IP, MAC, hostname or XML. Light retained two current mDNS names;
Deep retained a reverse-DNS name. Names remain unverified claims, not proven identity.

Both profiles passed refresh during work, history search/reopening, Run again
setup and widths 320/390/768/1440 px. No browser page errors or backend exception
tracebacks occurred. Deep retained its honest Running indicator while its device
check ran. Light's eight grouped checklist labels were all distinct. Real API
save/reopen/reset, keyboard focus, status filtering and next-step layout passed on
that isolated report; its factual JSON remained byte-for-byte unchanged. The test
checklist edit was reset to To check. Name/CVE cross-feature and delayed-response
regressions used synthetic responses, not extra live lookups.

Readability review confirmed the report states observations, limits, device-specific
first steps and user-owned review status separately. Windows feature names now have
reviewed meanings. Technical names, ports, original guidance and evidence remain
available. Long repeated action/role labels are still worth evaluating with real
readers; automation does not establish comprehension.

Artifacts: `.test-artifacts/fixes-live-20261006/` contains JSON, XML, timelines,
screenshots, browser/checklist results, integrity checks and `evidence-audit.json`.
Original normal reports and copied historical reports were byte-for-byte unchanged.
The owned test backend was stopped; a subsequent read-only process/port check
confirmed no listener remained on 8766. The normal backend was not restarted.

## Handoff and remaining work

The four confirmed application faults and implementable report improvements are
finished and verified above. Restart the normal VS Code backend task **when idle**
and refresh the browser to load the Python changes; these runs tested a fresh,
isolated backend rather than altering the already-running normal instance.

The previously intermittent Windows socket-reset issue remains unresolved. It did
not recur, which is not evidence of a fix. Keep its diagnostics and investigate a
supported runtime remedy if reproducible. Actual nontechnical-reader comprehension,
physical-phone/assistive-technology evaluation and authorised Ubuntu lab execution
remain pending; their protocols are updated, not their results. Pi-hole stays deferred.
