# Remaining fixes and simpler incomplete reports - 27 October 2026

Status: implemented, deployed and verified locally. WebKit navigation remains
deferred as requested; no full-matrix or new hosted-CI pass is claimed.

Scope: implement F1, F4, F2 and F3 from
[the fresh review](verification-review-20261027.md), plus the implementable report
usability recommendations. **F5/WebKit navigation is deferred at the user's
explicit request.** Its error collector, origin rules and CI matrix are unchanged.

## Execution plan

1. Share only compatible in-flight network snapshots across concurrent jobs;
   record query/queue timing and retain strict scope checks and failure latching.
2. Save terminal attempt metadata on normal return, task cancellation and errors;
   leave exit status unknown when no scanner result exists. Never count queued
   work as a probe. Finish attempt writes before finalising interrupted coverage.
3. Distinguish a network safety stop from a user cancellation and correct partial
   CVE cache wording. Simplify failed overviews, empty controls and repeated notes
   while retaining retry, coverage, technical evidence and accessibility semantics.
4. Separate live report-flow success from completed scan coverage in the verifier.
   Preserve the earlier failed pair and use isolated folders for new checks.
5. Run focused regressions, offline/package checks and Chromium/Firefox acceptance.
   Recheck authorised scope before a new Light/home and Deep/this-PC pair, without
   competing browser suites. Deploy to the normal app only when it is idle.

## Implementation

- `FreshNetworkReader` shares only unfinished reads for the same configured Nmap,
  scope and selected adapter. A later request always starts a fresh query, even in
  the same clock tick. Cancelling a waiter leaves other jobs' observations intact.
  Timeouts still stop affected guards; no stale authorisation cache, relaxed scope
  validation or increase to the interface-query deadline was introduced.
- Runtime diagnostics expose instance-level query/shared-read counts and executor-queue/query/
  total milliseconds. Failed-query logs retain the timing/reason without device
  identifiers. Supervisor shutdown drains any remaining shared read.
- Each started host attempt has one terminal record, including sibling-worker
  cancellation. Known duration/cause are saved, an unknown exit stays null, and
  shielded persistence finishes before coverage finalisation. Queued hosts retain
  zero attempts. Optional enrichment skipped before its stage gets an explicit
  `OPTIONAL_DETAILS_NOT_RUN` warning instead of appearing complete.
- Failed device cards distinguish network verification interruption from manual
  cancellation. Related CVE searches marked incomplete now say a new check requests
  fresh references. Completed-search wording is conditional rather than promising
  every saved result is cached.
- Failed reports lead with unassessed devices instead of a normal zero-feature
  summary; the source-bound report alternatives and prompt version **4.4.1** agree.
  Legacy evidence is preserved and old AI wording is not treated as current.
- Empty reports keep the coverage explanation, device/technical evidence and retry
  while hiding unused review search/filters, detail panels and zero-task checklists.
  Single-address reports hide unnecessary device search/sort. Device totals distinguish
  found/selected addresses, checked devices and unfinished checks.
- A shared cause is shown once, followed by an unfinished-device count and an
  expandable per-device list. Non-started work is labelled explicitly instead of
  "after 0 attempt(s)". Detailed evidence is still available.
- The live verifier saves separate `flow_passed`/`scan_pair_completed` values and
  supports `--require-complete`. An incomplete pair prints `LIVE_REVIEW_INCOMPLETE`;
  a successful UI flow alone cannot satisfy the opt-in complete-scan gate.

## Verification

Initial focused Python monitoring/evidence checks passed 70 cases; the expanded
focused set passed 26. Chromium/Firefox acceptance passed 74 cases across incomplete
reports, simplification, CVE, inventory, device context and parallel workflows.
Final frozen application build is `5ef8b4b9ad40e95f807b`, API contract 3. After
the prompt-version update, the offline gate
`.test-artifacts/checks-a7c6d7b7c0/` passed **1,008 Python tests** (five Windows
privilege skips/167 opt-in deselections), **305 JavaScript tests**, 30 syntax
checks, lint and 208-file formatting. Six final Chromium/Firefox incomplete-report
and scan/AI/retry workflows passed separately. This is focused acceptance, not a
new full browser matrix or a WebKit pass.

Fresh installed wheel `.test-artifacts/package-1343c9c2f9/` passed seven pages,
32 assets, synthetic create/reopen/delete/Undo and dependency consistency. Its
packaged source and prompt match the final application build. The preceding
package gate also passed before the prompt bump; it is not substituted for this one.

The security gate first detected a newly published tooling-only
[msgpack advisory](https://github.com/advisories/GHSA-j586-36cw-2gc2).
The application/dev graph was clean. `requirements-security.lock` and the idle
security environment were patched from 1.2.2 to **1.2.3** after verifying the
Windows wheel's official PyPI SHA256
`84a6616d396ec1bc18a1e83e67c96a393ec35dfe5e17434a5be7b9aa0fe988ab`.
Final `.test-artifacts/security-ce92814a40/` passed both complete dependency audits,
static analysis (16 low/zero medium-high) and secret checks (zero potential secrets).
Security-environment `pip check` and eight pin/graph tests passed. No advisory was
ignored; normal runtime dependencies were not changed for this tooling patch.

The normal app was confirmed idle through its authenticated running-scan endpoint,
then its exact process was verified, the tested final wheel installed, and the
backend restarted. Normal `pip check` passed; the public build/contract and all
served assets match source, with no restart required. No active job was stopped.
Fresh authorised Light/home and Deep/this-PC checks ran in
`.test-artifacts/rest-fixes-live-20261027/` with `--require-complete`. The helper
exited zero with both `flow_passed` and `scan_pair_completed` true. The earlier
failed pair remains unchanged.

## Fresh live verification

Light completed **10/10 discovered-device checks**, recording 12 answering
features and seven review items, with zero scan errors/warnings. Every selected
host has one attempt and one matching terminal record. Eight AI records (seven
items plus the overview) are ready under prompt 4.4.1. Two devices have reported
mDNS names; name availability is not an identity or safety guarantee.

Deep completed **1/1 selected this-PC check**, recording 14 answering features
and four informational review items, with zero scan errors. Its one warning is
the expected self-scan/local-routing limitation, not a failed network check.
Five AI records are ready under prompt 4.4.1. Light took about 304 seconds and
Deep about 527 seconds; these are observations, not promised completion times.

Read-only replay reproduced **171 service records, all 11 findings and two saved
certificate interpretations**. All **13 AI records** revalidated without rejected
fields or fallback reasons; inputs contained no recorded IP/MAC/hostname/raw XML.
There was no missing raw output for completed checks.

Exactly two scans were submitted. Both survived running refresh and opened reports
after analysis, with no page errors/overflow at 320/390/768/1440 px. Exports,
inventory filters/reset/return, feature and comparison sections passed. The isolated
test backend's launcher/child and port were independently confirmed stopped/closed.
The normal backend remains running, current, Nmap/Ollama ready and storage OK.
All **853 normal evidence files** stayed unchanged. No active normal job was stopped.

The monitor diagnostics already show real cross-job sharing (61 read calls joined
75 fresh queries at one checkpoint). No failed local-interface query has been
recorded in this pair. These are instance-level counters, not a claim about every
possible Windows load condition or a measured speedup against a controlled baseline.

F1's redundant competing reads, F4's worker-cancellation evidence gap, and F2/F3's
wording defects are implemented and tested. Actual network changes and unavailable
fresh observations still stop scans safely. Windows can still fail a real local
query; this change does not remove that safety boundary. The original root cause
was intermittent, so one clean pair is not proof against every future OS stall.
F5 is explicitly left open. Final integrity confirmed all 277 frozen app/test/
script/workflow/lock files unchanged after the documented tooling patch, and all
853 normal evidence files unchanged. Whitespace, lint and 208-file formatting
checks passed. No source files were removed or database introduced.

The first JavaScript checks exposed stale count/wording assertions and an overly
broad new safety-text regex; these were corrected while preserving uncertainty,
coverage and no-fabricated-claim assertions. The initial offline attempt passed
1,006 Python cases but stopped on an old network-safety wording assertion; the
subsequent gate passed 1,008 Python/305 JavaScript checks before the prompt bump.
Formatting-only failures were corrected before final gates.

No WebKit investigation or fix is included. Human-reader studies, physical
assistive-technology checks and the Ubuntu lab require their actual participants/
environment; automation does not complete those evaluations. Pi-hole remains
future work. No commit, push or hosted workflow rerun has been performed.
