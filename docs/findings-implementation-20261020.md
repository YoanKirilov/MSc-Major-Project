# Findings execution - 20-21 October 2026

Authorised follow-up to [the live review](live-review-20261020.md). Preserve all
normal reports and existing work; no commits/pushes, SQLite or OS trust bypass.

Execution order and acceptance:

1. Trust bootstrap: hash-verified pip 26.2.2 and certifi 2026.10.19; reconcile
   runtime/security pins; update only project environments. Patch fresh package/CI
   environments before online installs. Verify both standalone and vendored bundles.
2. Scan-start recovery: bounded JSON operation receipts, per-intention UUID,
   authenticated read recovery after lost replies/refresh; same intention cannot
   create two jobs, changed requests conflict, intentional new scans stay independent.
3. Verification freshness: compare running/expected build and contract; missing
   identity is unverified, not current. Do not stop normal work to verify this.
4. Plain language: shorten gateway role and unknown CVE mapping text, preserving
   uncertainty/technical evidence. Measure naming outcomes, without extra automatic
   probes or promises of complete device names. Human evaluation stays pending.
5. Verify isolated regressions, full offline gate, actual browser workflows,
   security and an installed wheel. Report live/synthetic checks separately.

## Implementation outcome

The code changes above are implemented locally. The normal backend still needs a
task restart; it has not been stopped or replaced. No commit, push or hosted run
was created. Historical clean/failed audits remain unchanged.

### Trust bootstrap

Updated runtime and security pins to certifi 2026.10.19. All three project
environments (`.venv`, `.venv-quality`, `.venv-quality-security`) now independently
report pip 26.2.2 and standalone/pip-vendored certifi 2026.10.19. Nothing was installed
globally and operating-system trust/security settings were not changed.

`scripts/bootstrap_trust.py` uses stdlib HTTPS, bounded downloads, pinned release
wheel hashes and an explicit target interpreter. Both wheels must verify before
installation; installation uses no index/dependency resolution, and a fresh process
checks both trust bundles. Missing/tampered offline wheels fail closed. Fresh CI,
package-test environments and README setup now bootstrap before online pip use.
Two public PyPI hashes were reviewed as secret-scanner false positives and only
their exact lines were allowlisted; no advisory or credential detector was disabled.

Primary release/incident sources:
[pip metadata](https://pypi.org/pypi/pip/26.2.2/json),
[certifi metadata](https://pypi.org/pypi/certifi/2026.10.19/json),
[certifi advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2),
[PSF incident guidance](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576).

### Scan-start recovery and freshness

New starts and unfinished-device retries receive an operation UUID before POST.
The coordinator reserves the scan UUID in atomic JSON before preflight. Concurrent
callers share one owned preparation task; disconnection does not cancel admission.
Repeated accepted requests recover the same scan, while changed settings, source
report or connection cannot authorise replacement work. Saved results stay separate.

An uncertain dashboard keeps Scan disabled and pins the receipt in its URL, including
when browser storage is blocked. Refresh/manual checks use GET only; bounded polling
stops after ten reads. Explicit reset warns that the original may exist and never
starts a new scan itself. Report retries also pin recovery before submission and
stay disabled during intermediate renders. Existing targeted retry eligibility is
unchanged: completed checks and silent/unselected discovery addresses are excluded.

Receipts are owned by the existing single-instance data root, file-locked and
bounded to 1 MiB/1,024 records, with at most five preparing tasks. There is deliberately
no automatic eviction. Corruption, lost primary with a retained backup, and full
capacity fail closed; saved reports remain readable. A durable maintenance/expiry
protocol remains future work: do not casually delete the journal to bypass capacity.
Legacy direct API starts without an operation UUID remain non-deduplicated.

The public verification helper compares running and expected source hashes as well
as API contract. Missing/unreadable identity is unverified, never presumed current.
Contract 3 prevents newer scan/retry/CVE requests reaching an older backend, without
blocking evidence reads or cancellation. During reopening, current source build
`9337b5f1a4d8df457b11` correctly differed from the normal running build
`3e5d3881e53f804e688b`/contract 2, producing `restart_required: true` despite matching
static assets. The isolated backend reported current build/contract 3.

### Plain-language changes and evaluation

The compact role is **Network connection device (name unconfirmed)**. Recorded-route
provenance remains in optional details, without inventing a verified router name.
Unknown CVE mapping now says the database did not provide enough detail to check
the software; related results remain unverified and no vulnerability was confirmed.
Neither change modifies findings, risk, evidence, scan scope or model validation.

Name availability/latency remain measured outcomes from the preceding live review.
No additional automatic name probes or traffic were introduced. Reader/actual-AT
tasks now explicitly include unknown scan starts and these shorter labels. Recruitment,
novice comprehension and spoken-output evaluation remain pending, not simulated passes.

## Verification

- Full offline gate `.test-artifacts/checks-7c70480217/`: **968 Python passed**,
  five Windows link-privilege skips, 153 opt-in cases deselected; **277 JavaScript**,
  29 syntax checks, lint and 202-file formatting passed. New tests cover concurrent
  starts, lost callers/replies, restart recovery, rejected preflight, changed settings/
  connections, removed reports, targeted retry, full/corrupt journals, shutdown and
  bootstrap/freshness boundaries.
- Chromium/Firefox focused run `.test-artifacts/final-start-browser-20261021c/`:
  **seven passed** (both-engine lost-start/refresh, both-engine response-policy tests,
  Chromium settings). The lost-response test uses a real backend and real accepted
  POST, then drops only its reply: refresh recovers one original job, with one POST
  total and no page errors. No Nmap/device/provider traffic is used in these cases.
- Parallel/settings browser run `.test-artifacts/parallel-browser-20261021.xml`:
  **16 passed**, zero failures/errors/skips. Actual Chromium/Firefox checked
  independent Light/Deep tabs, refresh/reopen, mobile/desktop layouts and settings.
  One Chromium settings case repeats the focused run above; counts describe executed
  cases, not 23 unique tests or a full hosted browser matrix.
- Final security `.test-artifacts/security-333f1a10c0/` (repeat of
  `.test-artifacts/security-de6b7a1f49/`): both complete pinned graphs report
  no known vulnerabilities; 16 low static alerts retained for review, zero medium/high,
  zero potential secrets. This is a local gate, not certification or hosted CI.
- Fresh installed wheel `.test-artifacts/package-93a66ec481/`: offline build/runtime
  environments bootstrapped with verified wheels; dependency consistency, seven pages,
  31 static assets and synthetic create/reopen/delete/Undo passed.
- Saved live evidence `.test-artifacts/live-review-20261020/verification-efa6eed885/`:
  reopened both reports at 320/390/768/1440 px, exports, inventory/filter reset and
  report-return context; zero page errors and **zero scan submissions**. Both saved
  test evidence and all protected normal evidence stayed unchanged. Owned backend
  shutdown was recorded; an independent check found its wrapper gone, zero listeners
  on its recorded port, and no matching owned Python process. Local Ollama/model
  readiness passed; no new model-generation
  or live network-scan result is claimed by reopening the saved pair.

Local Windows WebKit is still OS-blocked; no protection was weakened.
Ubuntu/reference lab, physical phone,
real AT, novice study and a new hosted matrix remain separate verification work.

## Deployment / resume

Finish active scans, restart **NetGuard: Start backend**, reopen its terminal session
link and reload existing tabs. Check Settings for API contract 3/current source before
new scans. Do not start a second server against the same JSON root. The first normal
restart/recheck and a future authorised fresh live pair are not claimed completed here.
