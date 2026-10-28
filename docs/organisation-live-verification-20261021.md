# Code organisation and live verification - 21 October 2026

Requested follow-up to [the four fixes](issue-fixes-20261021.md).

Plan / acceptance:

1. Make a small behaviour-preserving organisation change: move pure scan-start
   operation/generation ownership and bounded recovery-read state into a dedicated
   module. Keep DOM, storage, timers and requests in the dashboard. Protect all
   late-response/refresh behaviours with the existing acceptance tests.
2. Check source/asset reachability, imports, tests and package contents. Delete no
   file merely because its purpose is unfamiliar; preserve existing working-tree
   changes, historical evidence and household JSON.
3. Freeze source and confirm the current default-route network/this-PC address
   still match the authorised home scope before traffic. Use a new private data
   folder and owned backend, with Pi-hole disabled. Do not stop the normal server.
4. Run one Light/home scan and one Deep/this-PC scan. Verify saved coverage/errors,
   local AI wording against evidence, refresh, automatic report opening, mobile/
   desktop layout, exports and inventory. Do not conceal incomplete coverage or
   silently resubmit failed jobs.
5. Replay completed raw evidence/AI validation, confirm normal files unchanged and
   owned test-process cleanup. Record live, synthetic and hosted limits separately.

Organisation implemented: `static/js/start-state.mjs` now owns only operation,
generation, read ownership and the ten-read budget. It has no DOM/storage/network/
timer/authorisation effects. Dashboard orchestration delegates to it. Four added
pure-state cases and all 57 existing dashboard cases passed; the eleven source/
asset/API layout checks passed. No unused application files required deletion.

## Completed quality gates

- Full offline gate: `.test-artifacts/checks-83504c3796/`: 987 Python passes,
  five Windows privilege skips, 159 opt-in deselections; 296 JavaScript passes,
  30 syntax checks, lint and formatting of 204 Python files passed.
- Security: `.test-artifacts/security-4c8c18f3dc/`: both locked dependency graphs
  had no known vulnerabilities; static analysis recorded 16 low-severity findings,
  zero medium/high findings; secret detection passed. No protections were disabled.
- Fresh installed wheel: `.test-artifacts/package-91eeca8cc9/`: seven pages,
  32 static assets (including the new module), synthetic report creation/reopening/
  deletion/Undo and dependency consistency passed. Installation used the existing
  offline wheelhouse and hash-verified trust bootstrap.
- Actual Chromium/Firefox acceptance: 30 passes, zero skips/failures/errors in
  `.test-artifacts/organisation-browser-20261021.xml`. This includes scan-start
  recovery/late-response ownership, parallel workflows and Settings. Providers and
  device data in these acceptance cases are synthetic; this is not a live-scan,
  hosted WebKit or assistive-technology claim.

## Live execution and outcomes

Source was frozen at build `2e3a157beed5920419aa`, API contract 3. The current
default-route scope and this-PC address matched the previously authorised home
network. Exactly one Light/home and one Deep/this-PC scan were submitted to an
owned backend using `.test-artifacts/organised-live-20261021/data/`; Pi-hole was
disabled and the normal backend was not restarted.

Light stopped before completing discovery: `NETWORK_INTERRUPTED`, precise reason
`adapter_query_timeout`. The Windows connection-details subprocess exceeded its
eight-second limit. Discovery remains incomplete and no device checks are marked
complete; the one overview explanation finished with local Ollama. This is a
failed scan, not an empty successful network search. No automatic replacement scan
was submitted and no network guard was bypassed.

A subsequent read-only connection query succeeded in 2.477 seconds, returning
five connected rows. This does not establish why the earlier query timed out or
prove a network change. Further Windows-query reliability work should measure
fresh-query timing/contention while preserving fail-closed authorisation; do not
silently reuse stale snapshots or merely extend deadlines to hide the failure.

Deep completed its one selected this-PC check in approximately 544 seconds, with
14 open features, five findings (one low priority, four informational), zero scan
errors and six ready explanations. Its one warning correctly limits the result:
checking this computer through local routing does not prove that another device
or the internet can reach those services. This is not a vulnerability certification.

Read-only `scripts/audit_live_review.py` replay reproduced 21 Deep service records
and all five findings. Seven ready explanation records across the pair revalidated
with identifier-free model inputs, no fallback reasons and no rejected fields.
The failed Light report contributes one overview, not successful device checks.

Actual report checks passed at 320, 390, 768 and 1,440 pixels without horizontal
page overflow or browser errors. Both reports opened automatically after analysis;
two private exports, inventory filtering/reset and report return context passed.
Screenshots of the mobile card and failed Light overview were inspected. Light
explicitly says its search did not finish and does not claim no devices exist.

### Live acceptance limitation

The live helper exited **1**, not green: `refresh_kept_both_jobs` was false.
Light was already finished when first observed at 19.1 seconds, so the helper's
running-job refresh branch could not exercise it. Deep was refreshed while running;
this pair does **not** establish refresh preservation for both running scans. There
is no observed lost-progress bug here, but the unexercised assertion must not be
waived. The 30 synthetic browser acceptance passes are separate evidence. No helper
gate was weakened, and no further scans were submitted to manufacture a pass.

### Integrity, cleanup and deployment

- All **853** protected normal evidence files stayed unchanged. The **270-file**
  code/test/script/lock/workflow manifest matched before and after execution.
- Owned wrapper PID 16060 and server PID 23320 were independently absent after
  cleanup; owned port 13687 was no longer listening. No normal process was stopped.
- The normal app still exposes API contract 2/build `3e5d3881e53f804e688b`, unlike
  this tested contract-3 build. Finish active work, restart its task, reopen its
  session link and reload tabs. An isolated test pass is not normal deployment.
- Local HEAD observed after testing: `a131355`; no commit, push or hosted CI action
  was performed by this execution. No new hosted/WebKit or reader/real-AT pass is
  asserted. Private artifacts remain under `.test-artifacts/organised-live-20261021/`.

## Remaining work, in order

1. Investigate the eight-second Windows connection-query timeout with per-stage
   timings and bounded-process tests. Preserve fresh connection verification and
   truthful failure reporting; a later successful query is not a diagnosis.
2. On a later authorised run, verify refreshing a genuinely running Light job as
   well as Deep. Improve the helper's per-job observation timing separately, without
   treating an unobserved refresh as passed or masking product failures.
3. Reader evaluation: the explanations are simpler and fact-validated, but this
   is not proof everyone understands them. Consider leading an interrupted report
   with "No devices could be checked" instead of the current factual zero-count
   introduction, and explaining "encrypt"/"redirect" in the HTTP guidance.

No further application change was made during the frozen live execution. The
organisation change is verified; Light's underlying query reliability is not fixed.
