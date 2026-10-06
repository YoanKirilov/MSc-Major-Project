# Network continuity and unfinished coverage fixes — 4 October 2026

Addresses findings 1–3 in [the live recheck](live-recheck-20261004.md).

## Implemented

- Overlapping Windows adapter reads now share one bounded query across jobs and
  status requests. Each caller receives its own copy. Later requests perform a new
  query; there is no time-based cache that could authorise a changed network.
- Each scan guard also shares overlapping checks. Timeout, unavailable/ambiguous
  interface, malformed adapter output, actual snapshot mismatch, and delayed
  monitoring have distinct internal reasons. Reports preserve the reason and use
  wording that does not assert a network change when verification merely failed.
- Verification remains fail-closed: no automatic retry of active probes on stale
  context, no widened scope and no disabled network guard. A genuinely slow or
  failed Windows query can still stop a scan. This change reduces competing query
  load; it does not claim that every possible interruption has been eliminated.
- Cancelled host attempts retain `NETWORK_INTERRUPTED` when the safety guard caused
  them. User cancellation remains `HOST_SCAN_CANCELLED`. Pending checks closed by
  interruption retain their network-related cause as before.
- Report headlines and AI coverage wording count all unfinished selected or
  discovered device checks, including cancelled and unstarted checks. Silent,
  unobserved addresses in a discovery subnet are excluded. A partial report with
  no unfinished device checks uses a general limitation headline, never "0 devices
  could not be checked".
- Coverage counting is reusable within each language: the document property feeds
  Python report wording; the JavaScript helper feeds the title and coverage text.
  Regression cases protect the same semantics. Prompt version is now `4.2.2`, so
  older saved AI wording is not presented as currently validated. Existing scan
  evidence is not rewritten. Browser asset versions were updated.

## Verification

Focused regressions cover overlapping reads, fresh later reads, copy isolation,
failure latching, query-timeout diagnostics, real supervisor cancellation origins,
and cancelled/pending/skipped/failed/timed-out coverage in both selection modes.
The report renderer is tested against the misleading-zero headline case.
Read-only replay of the actual saved Light report now derives one unfinished check
despite its zero failure counter: "Checks finished for 7 devices; checks could not
finish for 1 device." The original JSON was not changed.

A read-only real Windows check after query coalescing served three simultaneous
requests with **one** adapter query in **3.97 seconds**, with matching outputs and
no errors. An earlier diagnostic caught an adapter-query timeout under load; the
new diagnostic path correctly distinguished it from a confirmed network change.
No new Light/Deep scan or external CVE request was run in this fix pass.

Final verification passed **427 Python tests**, one real-provider test deselected,
**51 JavaScript tests**, Chromium/Firefox/WebKit checks, lint/format for 121 Python
files, and nine JavaScript syntax checks. Artifacts:
`.test-artifacts/checks-58675364af/`. No new live-provider or full network-scan pass
is claimed; successful end-to-end Light/Deep completion still needs a live rerun.

## Loading and remaining scope

Restart the normal VS Code backend task when idle to load Python changes, then
refresh the report page. The normal backend was not stopped or restarted here.

The separately documented descendant-pipe timeout edge and annotation-backup
recovery improvement are not part of these three live-recheck fixes and remain
open. Do not interpret the earlier incomplete Light/Deep reports as passed scans.
