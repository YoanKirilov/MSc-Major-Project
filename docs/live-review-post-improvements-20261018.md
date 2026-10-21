# Post-improvement live review - 18 October 2026

Scope: investigation and recommendations only. No application fixes, data cleanup,
dependency upgrades, commits or pushes are authorised in this pass. Existing local
changes belong to the preceding implementation and are preserved.

## Execution and isolation

The detected default-route range and this-PC address matched the previously
authorised home scope before traffic began. One browser-submitted Light network
scan and one Deep scan of this PC run through a separately owned backend, using
current source and a new private JSON folder. Pi-hole is disabled. The normal
backend is not restarted or stopped. The working tree remains unpublished above
baseline `b49c71a66fec4a61b3f2be11e3565b50480b1265`.

Private artifacts: `.test-artifacts/live-review-20261018-c/`. Do not publish the
session log, identifiers, raw XML, screenshots or report text. A sandboxed Windows
adapter query first failed; the properly permitted read-only query succeeded.
That tool restriction is not classified as an application network-detection bug.

The 258-file source/lock/workflow manifest is saved privately in `source-manifest.json`.
Its canonical SHA-256 is
`a5184878b5367a1b4decd415e6efb764823bb2f9f7e2d6f4648b3667791cf12f`.
The browser test interpreter is Python 3.14.2. Scanner preflight reports Nmap 7.991;
the configured local model is `llama3.2:3b`.

Both scans and the browser/evidence checks completed. All 258 manifest entries
still matched after the review; no application/scanner/test source was changed.

## Live results and verification

| Check | Light network scan | Deep, this PC |
| --- | --- | --- |
| Discovered devices | 9 | Not a discovery scan |
| Selected device checks finished | 9 of 9 discovered | 1 of 1 selected |
| Unfinished device checks | 0 | 0 |
| Recorded open features | 12 | 13 |
| Review items | 8: four low, four informational | 4 informational |
| Recorded device-check errors | 0 | 0 |
| Duration including explanations | 259.4 seconds | 536.0 seconds |
| Ready explanation records, including overview | 8 | 5 |
| Fixed-wording fallback records | 1 (`not_simpler`) | 0 |

Both reports reached `phase=finished`/`analysis_status=ready`. The one Light
fallback is a validator decision, not a missing check or model outage. "Ready"
does not mean every sentence was rewritten; the model may select an original
reviewed alternative. Actual model calls occurred in this pair, unlike the previous
saved-only verification. No generated field was rejected in the ready records.

Deep recorded the expected `SELF_SCAN_LOCAL_ROUTING` warning: an answering program
on this computer does not establish exposure from another device or the internet.
Light's nine discovered devices are not a claim to have found every connected or
silent device. This PC was not present in Light's discovery result; Deep's recorded
name therefore is not evidence of a name being dropped for the same Light entry.

- `browser-results.json`: exactly two scan submissions; both active tabs survived
  refresh; both automatically opened their report after analysis; zero page errors.
- Both reports passed page-overflow checks at 320/390/768/1440 pixels. Private
  export previews, inventory views/reset and exact return-focus passed. The inventory
  contained ten separate saved observations in this isolated dataset. No label edits,
  deletion/restore operations, CVE web queries or name-refresh probes were sent to
  live devices in this verification.
- `integrity.json`: all **853** existing normal report/evidence files protected by
  the pre-run hash snapshot remained unchanged. `cleanup.json` recorded stopping
  the owned backend; its known loopback port was independently checked closed and
  its recorded parent/child processes were absent. The normal server remained running.
- `evidence-audit.json`: raw XML replay reproduced **155 saved service records**
  (including non-open states), all **12 deterministic findings**, host-script data
  and two saved certificate-date interpretations. No raw host evidence was missing.
  Thirteen ready explanation records passed validation. Selected model inputs
  contained no recorded IP/MAC addresses, hostnames or raw scanner XML. This replay
  checks consistency with source, not independent detection accuracy against a lab.
- Fresh offline gate `.test-artifacts/checks-817041122a/`: **938 Python passed**,
  five Windows link-privilege skips, 151 opt-in cases deselected; **270 JavaScript**,
  29 syntax checks, lint and 193-file formatting passed. The guarded suite ran while
  Deep was finishing; elapsed times are not controlled performance/SLA measurements.
- Focused actual Chromium/Firefox run `.test-artifacts/review-browser-20261018/`:
  **16 passed** covering CVE lookup/lost-response/cache recovery, enforced response
  headers, native controls, keyboard/dialog/text spacing and no-JavaScript guidance.
  These are synthetic provider/scanner workflows, not extra live scans or a full
  browser/OS matrix. Local Windows WebKit remains OS-blocked and was not retried.
- Security `.test-artifacts/security-14c973b716/` passed: no known vulnerabilities
  in either audited dependency graph, zero medium/high static alerts, zero potential
  secrets. All 16 low static alerts remain recorded. No dependency was upgraded.

The previous installed-wheel check remains historical evidence from the preceding
implementation; it was not repeated in this review. No new hosted run, physical-phone,
true-zoom, assistive-technology or participant evaluation was performed.

## Plain-language review

The displayed overviews explain "features" with everyday examples and preserve
counts and limited coverage. Light's visible first action tells the reader to check
ownership and a device web address; the adjacent precaution says not to enter
passwords on HTTP or bypass certificate warnings. Deep offers conditional Windows
Security steps, explicitly says not to disable the firewall/core services, and
keeps the self-check limitation visible. Optional reasoning is separate.

This is an assistant walkthrough, not evidence that all nontechnical people
understand it. "Network gateway (recorded route...)" remains dense in the first
action, and CVE/fingerprint/version terms need the existing optional explanations.
Prefer testing shorter role labels and concrete first steps over adding more
filters/controls. Keep technical evidence accessible and never infer router/device
identity or a verified vulnerability merely to simplify the text.

## Deployment finding: normal backend has not loaded the new contract

Read-only `/openapi.json` on the normal server has no request body/operation-ID
schema for the CVE POST. Current source explicitly declares `CveLookupRequest`;
the fresh isolated backend exposes it. Static assets match source, so matching
browser files do not establish that the Python process has reloaded backend code.
The normal server still sends the expected CSP/nosniff/framing/referrer/no-store
headers; the earlier header finding is not reopened.

Immediate action: finish active work, restart **NetGuard: Start backend**, then
reload tabs and check the schema/build again. The audit does not stop an unrelated
server. These live tests exercise the newly started isolated current-source
backend, not an upgrade of the normal running process.

Recommended follow-up: expose a non-secret running build/contract identifier in
status/Settings and compare expected client/API versions. Extend the helper's
normal-server preflight beyond route/static-byte checks to detect this mismatch.
Do not block access to saved evidence or infer freshness from static files alone.

## Reproduced application edge cases

These use synthetic data, not the connected home devices or a public CVE request.
The probes assert the observed defect; a passing reproduction is not a fix.
Initial artifacts: `.test-artifacts/review-probes-run-20261018/` (two reproductions).
Final `.test-artifacts/review-probes-confirmed-run-20261018/` passed **three observed-
behaviour reproductions**, including the DNS mechanism below. Network/scanner/provider
work was blocked, NVD was mocked, and all created JSON was isolated.

### F1. Medium: queue-expired checks cannot use targeted retry

`app/jobs/transitions.py::close_unfinished` deliberately records an unattempted
queue-expired target as `skipped`, with `scan_queue_expired`. This correctly
preserves unfinished coverage. But the retry eligibility lists in
`app/api/scans.py::retry_unfinished_hosts` and `app/static/js/scan.js` exclude
`skipped`. The real in-memory API probe recorded one unfinished target and returned
HTTP 409, "There are no unfinished device checks to retry." No scan was started.

Effect: a rare capacity/queue expiry has a misleading recovery response, and the
targeted retry action may be hidden. Run again remains a possible broader workaround;
this is not evidence of lost JSON or a completed security check.

Proposed fix: share an explicit retry-eligibility policy across server/presentation.
Include reason-qualified skipped targets such as queue expiry when still within
the authorised scope. Do not indiscriminately include every skipped/silent address.
Retain current scope/interface/permission/revision/profile/admission checks.

Acceptance: a mixed completed/queue-expired report retries only the eligible
unfinished target; deliberate exclusions and silent discovery addresses stay out.
The old report remains unchanged and no retry starts automatically.

### F2. Medium data-status edge: empty CVE mapping nodes become "no matches"

`app/scanner/cve.py::NvdClient.lookup` recognises missing/empty top-level
`configurations`, but a nonempty list containing empty mapping nodes bypasses
that guard. `_related_to_product` returns false, yielding `related_status=no_matches`
and `related_unverified=0`, despite there being no usable applicability criteria.

The mocked record used `configurations=[{"nodes":[{"cpeMatch":[]}]}]` and produced
exactly that result. This does not establish that the live NVD service returned
this shape today. The interface still warns that no matches do not prove safety;
no fabricated vulnerability or safe-device verdict was observed.

Proposed fix: return a bounded tri-state applicability outcome: positive relation,
usable nonmatching mapping, or unknown/unusable mapping. Treat malformed/empty
nodes and exhausted traversal budgets as unknown. Preserve version references and
separate related leads; do not broaden port guesses or affected-version claims.

Acceptance: missing/null/empty/empty-node mappings and traversal exhaustion remain
unknown; a usable different product remains nonmatching; negated/rejected records
never become positive matches. No private identifier enters the query or model.

### F3. Medium architecture risk under load: DNS timeout does not stop shared-thread work

`ScanSupervisor._local_hostname` bounds its await to one second around
`asyncio.to_thread(socket.gethostbyaddr, ...)`. A native resolver already executing
does not stop merely because that await times out. JSON I/O also uses the loop's
default executor, so enough lingering DNS calls can compete with storage/progress
work. Python documents that a [running thread future cannot be cancelled](https://docs.python.org/3.14/library/concurrent.futures.html#concurrent.futures.Future.cancel).

The isolated single-worker probe used a fake resolver blocked on a test event.
The hostname await returned `None`, but the resolver thread was still occupied;
an unrelated `to_thread` task could not run until the event was released. No real
DNS request occurred. This proves the shared-worker mechanism, not that the default
pool saturated or caused a live failure in this nine-device run.

Proposed fix: isolate and bound name-resolution admission/workers from storage;
prefer a truly timeout-aware/cancellable resolver transport where feasible. Preserve
unknown names and record per-source not-found/timeout/error outcomes. Simply raising
the await timeout or executor size is not a resource-isolation fix. Keep bounded
shutdown and do not resolve arbitrary names/addresses outside the authorised scope.

Acceptance: many deliberately blocked synthetic DNS requests do not delay progress
JSON, cancellation or saving a finished report. Running/queued resolution work remains
bounded and shutdown has an explicit tested policy. Do not present late names as
current verified device identity.

## Recommendations after the reproduced fixes

1. Make uncertain CVE recovery robust across two tabs. Currently each service
   retains only its latest operation receipt. A second cached request can replace
   a first tab's receipt, leaving that tab unable to correlate a lost reply through
   GET recovery. Keep uncertainty truthful, but consider bounded operation-status
   receipts rather than relying on a single overwritten field. Do not auto-repeat
   POSTs or change the original reference date.
2. Prioritise measured novice/assistive-technology evaluation over more controls.
   Ask users to explain what was found, what remains unknown and their first step;
   exercise actual screen-reader announcements and dialog focus return. W3C's
   [status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
   and [modal-dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
   inform the checks, but automated DOM/viewport tests are not a conformance study.
3. Extend the measured cache work to rich histories and simultaneous inventory,
   active scan writes and cancellation. The 600-report benchmark reduced full
   reads, but search still examines the library and that experiment did not measure
   a live scanner cancellation deadline. Keep authoritative JSON and bounded caches.
4. When explicitly ready to publish, run the current split CI matrix on the new
   revision and review retained redacted artifacts. The older green baseline does
   not verify unpublished changes; local WebKit's OS protection must stay enabled.
5. Improve naming diagnostics before promising more names. This Light run named
   only one of nine devices (mDNS); Deep named this PC by reverse DNS. Absence of a
   name is not an intruder verdict. The isolated run deliberately did not import
   normal nicknames/history. Measure per-source availability, timeouts and latency
   in the existing name-only refresh instead of assuming rich mDNS must reveal
   every name or deploying deferred Pi-hole. The DNS mechanism above is a risk,
   not an established explanation for this run's name coverage.

Recommended order: restart the stale normal backend when idle; fix/test F1-F3 in
small steps; then improve cross-tab receipts/build diagnostics, measured naming and
reader/AT evaluation. Keep FastAPI, local JSON and the current simple UI. There is
no evidence from this review requiring a framework/database migration or broader
network probing. All application fixes remain unimplemented in this audit.
