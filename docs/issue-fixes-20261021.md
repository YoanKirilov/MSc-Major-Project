# Four live-review fixes - 21 October 2026

Authorised follow-up to [the review](live-review-20261021.md). Scope: implement
F1-F4, preserve existing work and saved evidence, and verify isolated regressions,
browser workflows, security, package and saved-report display. Do not restart the
normal server or submit additional network scans merely to complete these fixes.

Execution order / acceptance:

1. Correlate every scan-start POST/GET completion with the current operation and
   UI generation. Old success, rejection, timeout and read finalizers must not clear,
   enable or replace a newer start, whether the newer one is pending or accepted.
2. Restore pending-start recovery before scanner readiness. Only read the original
   receipt; keep recovery available under transient status/receipt outages. Expired
   sessions retain context and stop automatic reads rather than enabling Scan.
3. Preserve bounded known Nmap interface reasons through snapshot/guard/report
   storage. Distinguish list timeout, execution failure, unavailable/invalid output,
   unmatched scope and ambiguity. Keep fail-closed cancellation and deadlines.
4. Distinguish incomplete/unrecorded discovery from a completed search with no
   answers in the summary, metric and technical empty state. Do not change evidence
   counts, severity or accepted AI records.

## Implemented

F1: dashboard starts and receipt reads now carry operation/generation ownership.
Superseded POST outcomes, readiness reads and GET finalizers cannot change the
current URL, pending key, error/disabled state or selected job. Reset does not cancel
the earlier scan or grant permission to repeat it. Recovery reads are owned per
generation, so an older pending read cannot block/unlock a newer one. Rejected
receipts cannot leave the next start's recovery control disabled. A malformed start
reply stays uncertain and recovers its original receipt, not a replacement scan.

F2: a pinned start restores its controls before any readiness query and reads its
original authenticated receipt directly. Scanner/AI `/status` availability is not a
prerequisite for accessing saved progress. Transient read errors retain bounded
GET-only recovery. Expired sessions keep the operation URL, explain how to reopen
the session and stop automatic reads; Scan is not enabled as an alternative.

F3: Nmap list timeout, unavailable/execution failure, oversized output, unmatched
scope and ambiguous/missing interface now remain distinct known reason codes through
the snapshot and saved guard failure. Unknown reasons fall back to a bounded generic
code, never raw output. The local list query retains its five-second deadline;
oversized output is rejected. Optional announcement wording no longer calls a list
failure a scope mismatch. Guard failure still cancels/stops scanning: there is no
stale-authorisation cache, deadline extension, scope broadening or automatic retry.
The exact cause of the historical Light failure cannot be reconstructed retroactively.

F4: interrupted discovery now says the device search did not finish, with **Search
incomplete** instead of **0 of 0**. The technical empty-device table uses the same
honest explanation. A completed empty discovery still says no devices answered;
legacy missing completion metadata stays explicitly unrecorded. Partial discovered
results retain their counts with a caution that other devices may be missing.
These are display changes, not edits to saved evidence or accepted AI records.

The broader recommendations (receipt maintenance, reader studies, fresh shared
query measurement and empty-report redesign) remain separate work. No framework,
storage or model-validation policy change was needed.

## Verification

- Final offline gate `.test-artifacts/checks-7d9dd14a76/`: **987 Python passed**,
  five Windows link-privilege skips, 159 opt-in cases deselected; **292 JavaScript**,
  29 syntax checks, lint and 204-file formatting passed.
- New focused real-browser run `.test-artifacts/issue-fix-browser-20261021b.xml`:
  **14 Chromium/Firefox cases passed**, zero failures/errors/skips. It covers old
  accepted/409/503 POSTs after a separate start, 401/503 receipt recovery without
  `/status`, interrupted summaries/metrics/tables at 320/390/768/1440 px, and the
  existing real-backend lost-start-reply/refresh workflow. All scan/provider replies
  are synthetic; original fixture evidence is checked unchanged.
- Initial harness runs exposed a request-event/route-dispatch timing difference in
  Firefox and a cross-realm microtask assumption. The harnesses now wait for actual
  route/read entry, not a guessed single tick; the final focused run passed. Those
  initial failures were not hidden or presented as application regressions.
- Installed wheel `.test-artifacts/package-8dde289538/`: verified trust bootstrap
  and dependency consistency passed in fresh offline environments; seven pages,
  31 static assets and synthetic create/reopen/delete/Undo passed.
- Saved reports `.test-artifacts/live-review-20261021/verification-c07c1a082f/`:
  zero scan submissions/page errors, four responsive widths, exports/inventory and
  return context passed. Both saved test and protected normal evidence stayed
  unchanged. The interrupted Light report visibly says **Search incomplete** and
  **The device search did not finish**. Seven saved AI records and 21 Deep service
  records/five findings revalidated without new model generation or device traffic.
  Owned wrapper/server PIDs 24672/15484 were independently absent and port 20668
  had no listener after shutdown. The normal backend/session was untouched.

- Final security `.test-artifacts/security-200a9b7118/`: both complete pinned
  dependency graphs have no known vulnerabilities, 16 low static findings remain
  recorded for review, zero medium/high static findings and zero potential secrets.
  No advisory suppression, environment upgrade or TLS/OS-security bypass was used.

- Broader workflow run `.test-artifacts/fix-workflow-browser-20261021.xml`:
  **16 Chromium/Firefox cases passed**, zero failures/errors/skips. Independent
  Light/Deep tabs, refresh, analysis waiting, failed-check retry/history, known-host
  rerun setup and settings passed at mobile/desktop sizes. Together with the focused
  run above, **30 distinct parameterised browser cases passed**. Network/AI replies
  remained synthetic; this is not a hosted matrix or a fresh live scan pair.

## Deployment and limits

Current app source build: `b4cbbac50592fadd514e`, API contract 3. The normal process
still reports `3e5d3881e53f804e688b`/contract 2. Finish active work, restart
**NetGuard: Start backend**, reopen its terminal session link and reload tabs. Do
not run two servers against the same JSON folder. No commit, push or new hosted CI
run was made. Local Windows WebKit remains OS-blocked, with protections unchanged.

No new live network scans or AI generations were submitted in this implementation
pass. The earlier Light interruption is preserved, not relabelled successful. A
future authorised live recheck can verify current network-query behaviour with the
new diagnostics. Actual novice/AT/physical-device and Ubuntu reference-lab evaluation
remain pending; automated passes are not certification.
