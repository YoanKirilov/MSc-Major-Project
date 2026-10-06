# Light and Deep live recheck — 4 October 2026

## Scope

User-requested Light scan on the previously authorised home network
`192.168.0.0/24`, verified against the current Wi-Fi adapter. Deep targeted this
Windows computer at `192.168.0.216`, not the standby Sony. An isolated backend on
port 8766 used `.test-artifacts/both-recheck-20261004/data`. The normal backend and
its saved history were not changed. No external CVE lookup was submitted.

## Actual results — neither is a complete successful scan

| Profile | Result | Evidence |
| --- | --- | --- |
| Light | Partial, 210.6 seconds | Eight devices discovered, seven checks completed, one cancelled by the network guard; ten open services and seven review items saved. |
| Deep | Failed, 30.3 seconds | Network guard stopped work before a host attempt completed; zero assessed devices is not a clean security result. |

Light ID: `c42a0b2a-5beb-4fe3-a5c4-f477809fe488`.
Deep ID: `99a62b67-9dc2-4bc1-a2ce-1f413ee5f389`.

Both reports remained readable. Refresh, history reopen, 320/390/768/1440-pixel
layouts, and Run again navigation passed without browser errors or extra scan
submissions. The isolated server was stopped after it became idle.

Saved Light XML replay matched 105 service-state records and seven rule findings.
Six Light AI records passed independent revalidation; two retained reviewed wording
because the alternatives were not simpler. Deep's incomplete-report explanation
also passed revalidation. AI inputs contained no device IP, MAC or hostname.

## Findings and recommended implementation order

1. **Network-check availability and diagnostics (high priority).** Both live jobs
   recorded `NETWORK_INTERRUPTED`. A subsequent read-only snapshot was unavailable;
   the next two matched the original snapshot exactly. Three later standalone
   Windows queries succeeded in approximately four seconds each. The original
   failure cause is not retained, so this does not prove whether it was a timeout,
   adapter-query error or transient connection change. `windows_connections()`
   collapses these causes to `None`; `NetworkGuard.check()` treats unavailable
   snapshots as a mismatch. Preserve structured reasons, avoid overlapping
   expensive adapter queries, and test transient unavailability under load.
   Any recovery must pause probing and require fresh verification; do not disable
   the guard, silently accept a changed network, or simply keep scanning on stale
   context. Regression tests ran concurrently here; load-related sensitivity is a
   hypothesis, not a confirmed root cause.
2. **Incorrect unfinished-device count (confirmed).** Light's headline says
   "Scan finished; 0 devices could not be checked", but its coverage correctly
   reports seven of eight completed and one cancelled. `static/js/scan.js` uses
   only `service_failed_count`, excluding cancelled or unstarted selected checks.
   `explanations/report.py` uses that same counter for its check-summary wording.
   Introduce consistent coverage-derived unfinished counts for UI and AI inputs;
   exclude unobserved discovery addresses, and test cancellation, restart, queue
   expiry, and interruption. Keep the original statuses and causes intact.
3. **Preserve interruption provenance at target level.** The Light target records
   `host_scan_cancelled`, while the report-level cause is `NETWORK_INTERRUPTED`.
   Distinguish a user cancellation from a safety-guard cancellation in target
   details, so the user understands why retrying requires network verification.
4. **Previously confirmed subprocess deadline edge remains.** Output draining can
   exceed the timeout when descendants retain inherited pipes. Add bounded drain
   cleanup and a regression without discarding captured evidence. This was not
   the observed failure in these live jobs.
5. **Previously noted annotation recovery remains.** Validate and recover the
   existing annotations backup when appropriate, without silently overwriting it
   with corrupt primary content or losing revision-conflict protection.

Name enrichment did not finish after the Light interruption. Missing names in this
report are therefore not evidence that the naming implementation itself regressed.

## Code organisation and regression checks

Reviewed command profiles, subprocess lifecycle, network continuity, enrichment,
coverage transitions, report wording, JSON annotations and CVE request boundaries.
No source module, template or static asset was identified as safely unused.
Existing module/asset reachability checks passed; no speculative deletions or
behavioural refactor were made. A worthwhile later organisation change is to
centralise coverage semantics before changing the count-related presentation.

`scripts/check.py --browser --browser-engines chromium,firefox,webkit` passed:
409 Python tests, one real-provider test deselected, 50 JavaScript tests, lint and
format for 120 Python files, and nine JavaScript syntax checks. Artifacts:
`.test-artifacts/checks-fc93cf3f95/`. These passing tests do not override the failed
live completion results above. New regressions are needed for the newly observed
cases. No implementation fix is claimed in this review.
