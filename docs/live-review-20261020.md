# Live scan and architecture review - 20 October 2026

Scope: investigate and record findings/recommendations. No application fixes,
dependency upgrades, cleanup, commits, pushes or normal-server restart in this pass.
Existing working-tree changes and household reports are preserved. Keep FastAPI,
local JSON and current scope/permission/admission protections.

## Highest-priority finding: certificate trust dependency

**The security gate failed.** It reported `PYSEC-2026-4320`, alias
`GHSA-6q48-6c7w-9gw2`, for `certifi==2026.7.22` in both dependency graphs.
The installed app, quality and security-tool environments have that version.
Pins are in `requirements.lock:7` and `requirements-security.lock:5`; the other
project lock graphs include these files rather than needing conflicting new pins.

The [maintainer advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2)
rates the compromised-certificate trust issue Critical. Python's
[security announcement](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576)
recommends `certifi>=2026.10.19` and `pip>=26.2.2`. It explains the
2026.10.18/2026.10.19 distinction: the latter retains unaffected roots for
compatibility. The [2026.10.19 release](https://pypi.org/project/certifi/2026.10.19/)
is available. This advisory was published today; yesterday's recorded clean audit
must not be rewritten as though it had detected it.

The three checked project environments have pip 25.3. Runtime pip separately
bundles certifi 2025.10.05. Updating the app's standalone certifi alone would not
update pip's vendored bundle. Treat the bootstrap tooling as part of this fix.
Do not disable TLS checks, edit the CA bundle by hand, suppress the advisory or
assume Windows system trust alone fixes these clients.

Impact: HTTPS clients using the affected bundle can trust certificates associated
with compromised intermediate CA keys. The app's public NVD HTTPX client uses
default TLS verification, so this dependency matters. Exploitation requires the
conditions described by the advisory; this audit did not demonstrate interception,
a compromised PC, or a vulnerability on a household device. Local HTTP Ollama
processing and Nmap observations are not invalidated merely by this dependency
finding. No real NVD CVE query was issued in the live pair.

Recommended fix/acceptance, **not executed**:

1. Obtain patched pip/certifi through an independently verified download/hash path
   following the official guidance; do not bootstrap by disabling verification.
2. Reconcile both certifi pins and update the three project environments, with
   pip's own bundle addressed separately. Avoid unrelated framework upgrades.
3. Refresh the owned offline wheelhouse/bootstrap procedure. New package-test
   environments created by `venv.EnvBuilder(with_pip=True)` also need a patched
   bootstrap before any online installation; do not blindly reuse old artifacts.
4. Run `pip check`, both dependency audits, offline tests and a fresh installed-wheel
   verification. Confirm the advisory disappears without an ignore rule and retain
   normal HTTPS verification. Restart the app only when active work has finished.

Security artifacts: `.test-artifacts/security-757ef62a13/`. There was one distinct
affected package in each of two graphs, not two different vulnerabilities.
Static checks retained 16 low alerts, zero medium/high alerts and zero potential
secrets. These clean subchecks do not make the overall security gate green.

## Execution and current running architecture

The detected default-route range/this-PC address exactly matched the previously
authorised home scope before traffic began. One Light scan and one Deep scan of
this PC were submitted through a separately owned backend and new JSON folder:
`.test-artifacts/live-review-20261020/`. Pi-hole remained disabled. No existing
normal nicknames/history were imported into the isolated dataset.

Normal public preflight now reports API contract **2** and running build
`3e5d3881e53f804e688b`, matching current app source. Served assets match too.
The earlier normal-process restart finding is therefore closed for this snapshot;
no restart was performed by this review. Passing source freshness is not a release
or security certificate. The source remains unpublished above baseline
`b49c71a66fec4a61b3f2be11e3565b50480b1265`; no new hosted CI result is claimed.

The design still uses one owned data folder, five admitted jobs, two scanner
workers and one analysis slot, with private-address name workers isolated from
the JSON executor. No evidence here calls for replacing FastAPI or adding SQLite.
Snapshot/scoped retry validation and original-versus-annotation separation remain
important protections, not candidates for deletion during code organisation.

## Live results

Light finished 8 of 9 discovered device checks, saved 8 device results, found 12
open features and recorded 8 review items. Duration including explanations was
336.7 seconds. One selected address was unreachable on both attempts (about 1.97 s
each). Both attempt XML files record zero up/one down and no host element; the
ledger correctly records `HOST_UNREACHABLE`, rather than a successful empty check.
The actual cause (sleep, disconnection, blocked discovery, or something else) was
not established. There was no automatic third attempt or extra targeted retry.

This is an incomplete device check, not proof that the entire scan crashed, and
must not be hidden by labelling everything complete. The targeted retry policy
can offer a later explicit retry without repeating completed targets. Two device
names were recorded in this Light run; lack of a name is not an intruder verdict.

Deep completed its selected this-PC check in 550.3 seconds including explanations:
13 open features, four informational review items, zero check errors. The sole
warning is the expected `SELF_SCAN_LOCAL_ROUTING` limitation: an answer from a
program on this computer does not establish access from another device or the
internet. This PC was not a Light result, so its Deep name is not evidence of a
name being dropped for the same Light entry.

| Verification | Light network | Deep, this PC |
| --- | ---: | ---: |
| Finished device checks | 8 of 9 discovered | 1 of 1 selected |
| Open features | 12 | 13 |
| Review items | 8: four low, four informational | 4 informational |
| Ready explanation records, including overview | 8 | 5 |
| Fixed-wording fallback records | 1 (`not_simpler`) | 0 |
| Replayed saved service records, including non-open states | 120 | 20 |
| Names/source | 2/mDNS | 1/reverse DNS |

Both reports reached finished/analysis-ready and real local model calls occurred.
The one fallback is a wording-validation decision, not a model outage or missing
device check. Ready does not mean every sentence was rewritten; the model can keep
reviewed original wording. Thirteen ready records revalidated with zero rejected
fields; selected model inputs contained no recorded IP/MAC, hostnames or raw XML.
The replay reproduced all twelve deterministic findings and two saved certificate-
date interpretations; completed checks had no missing raw host evidence. This is
source consistency verification, not independent lab detection accuracy.
Discovery replay also reproduced all nine Nmap observations; their union with
the two mDNS-observed addresses exactly matched the nine observed ledger targets.

All eight Light reverse-DNS requests timed out within at most 2,017 ms; four mDNS
observations supplied two recorded device names. Deep returned this PC's name in
134 ms. These are measured source outcomes, not an established explanation for
why each external device did not answer PTR queries or a guarantee of complete
device identity. No optional name-only refresh was added to this live pair.

Exactly two browser scan submissions occurred; refresh retained both jobs without
duplicate submission, and each report opened automatically after analysis. There
were zero page errors or report overflow at 320/390/768/1440 px. Export previews,
inventory view/reset and exact report-return context passed. The isolated inventory
contained ten saved observations, including the unfinished address; it is not a
claim of ten presently connected physical devices.

All **853** protected normal report/evidence files stayed unchanged. The owned test
backend stopped after both jobs finished; a separate read-only check found its port
closed and recorded parent/child processes absent. Normal app/session ownership
was untouched. No ERROR/traceback/unretrieved-task entry was found in the owned
backend log. A 263-file app/test/script/lock/workflow manifest stayed byte-identical;
only this review's private probes/artifacts and documentation were added/updated.

### Plain-language walkthrough

The visible Light headline is "Scan finished; 1 device could not be checked", with
the cause qualified as unknown, two attempts and an explicit targeted retry option.
It does not hide unfinished coverage or call the whole scan successful. The visible
overview explains features with web-page/file-sharing examples. Technical saved
model fields can retain original wording while display-only equivalents remain
plain; this must not be misreported as every sentence being generated by AI.

First actions retain HTTP/certificate precautions. Deep explicitly says not to turn
off the firewall/core Windows services to remove a result. The gateway-role sentence
is still dense, and optional CVE terminology can be clearer (recommendations below).
These are assistant reading observations, not measured novice comprehension or a
completed accessibility assessment.

## Additional reproduced issues

These are synthetic observed-behaviour probes, not extra device scans or fixes.
Private source and results are under `probes/`, `probe-run/` and
`probe-results.xml` inside the live-review artifact folder. Both Python probes and
the JavaScript probe passed by reproducing the weaknesses. Nmap/provider/device
work was blocked; their passing result does not close the findings.

### F1. Medium: uncertain scan start can be submitted again

`app/static/js/dashboard.js:173` re-enables Scan whenever `activeScanId` is absent.
The start request sets that ID only after receiving the POST reply. A lost reply
therefore hides progress and returns an enabled Scan button, with no pending
operation receipt. The existing timeout message warns against a duplicate, and
the app does **not** retry automatically. Nevertheless, a second explicit click
can issue a new request before the first attempt is identified.

The frontend probe reproduced two explicitly clicked submissions after a synthetic
lost reply, an enabled button and no stored recovery receipt. The real synthetic
API probe submitted the same valid body twice and captured two different admitted
UUIDs (no scanner executed). Two intentional scans are valid; the bug is the lack
of distinction between a new intention and recovery of an unknown first outcome.
Neither live browser submission in this review lost its reply.

Recommendation: create an operation ID before an explicit scan-start intention;
persist a bounded, authoritative operation-to-scan receipt under existing admission
and JSON locking. Keep uncertain state across refresh and recover by authenticated
reads. Do not guess from a matching address or arbitrarily attach another tab's
job. Changed target/profile/scope with a reused key must conflict, not silently
reuse permission. Intentional Run again gets a new operation ID. Preserve current
CSRF/origin/scope/network guards, no automatic POST retry and access to saved data.

Acceptance: lose a reply before/after admission, refresh, repeat from another tab
and simulate slow preflight; one intention produces at most one job. A distinct
intention can still run in parallel. Never recover onto another authorised scope
after a connection change. This extends the current CVE recovery principle; it is
not a claim that the existing lack of automatic POST retries violates HTTP.
See [RFC 9110, idempotent methods](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2).

### F2. Low: normal-server verification can miss a same-contract older build

`scripts/live_review.py:132` determines `restart_required` from the CVE request
schema and contract number alone, despite recording the build header. A mocked
server with contract 2 and a different older build returned `restart_required=false`.
This is a verification blind spot, not evidence today's matching normal server is
stale. The app's authenticated status separately compares source freshness.

Recommendation: compare the normal running build with the expected current source
build as well as the API schema/contract. Record expected/running IDs and a tri-state
freshness outcome; missing/unreadable identity is unverified, not a clean match.
Acceptance: same-contract different build, missing header, unreadable source and
genuine match all produce distinct truthful outcomes. Do not stop the normal app
or block access to saved evidence merely to make a verification helper pass.

## Improvements, after the fixes

1. Shorten the gateway-role sentence in the first-action section and put the
   recorded-route explanation in existing optional details. Test an everyday role
   label with readers; do not infer a verified router/device name from the route.
2. Use everyday wording for unknown CVE applicability (for example, "The database
   did not give enough detail to check this software"), retaining the explicit
   no-confirmed-vulnerability and limited-search cautions. Keep product mapping and
   fingerprint terminology in optional technical details rather than extra filters.
3. Continue measuring name-source availability, latency and timeout outcomes.
   More mDNS questions or guessed manufacturer names cannot guarantee identification.
   Test a bounded, optional longer name-only retry before increasing every Light
   scan's traffic/deadline, and keep returned claims distinct from verified identity.
4. Prioritise the prepared novice/disabled-reader/real-AT evaluation over more
   controls. Include the unfinished-device headline, uncertain scan start and
   recovery message, correct focus return and one useful announcement. Automated
   role/viewport tests do not establish spoken output or universal comprehension.
   [W3C status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
   supports non-focus-stealing accessible status updates, not repeated elapsed ticks.
5. Before publication, fix the trust dependencies, then run the current hosted
   platform/browser matrix with retained redacted synthetic failure evidence.
   Do not weaken local WebKit protections or upload household reports/session logs.

Recommended order: **certificate/tooling trust update first**, uncertain-start
recovery second, verification freshness third; then measured wording/naming/user
evaluation. The recommendations remain unimplemented in this review.

## Verification and limits

- Offline gate `.test-artifacts/checks-0670d898c7/`: **957 Python passed**, five
  Windows link-privilege skips, 152 opt-in cases deselected; **274 JavaScript**,
  29 syntax checks, lint and 197-file formatting passed.
- Focused Chromium/Firefox run `.test-artifacts/review-browser-20261020/`:
  **16 passed**, zero failures/errors/skips.
  It covers the actual engines, not merely job labels, with synthetic providers.
- The security gate failed as described above. No installed-wheel rebuild or
  dependency installation was repeated using the now-flagged lock/bootstrap.
  Yesterday's installed-wheel result is historical, not a new secure package pass.
- No real participant, physical phone, true-zoom, screen-reader or independent
  reference-lab evaluation was performed. No broad unused-code deletion was made;
  the audited fixes/protections should not be removed as if they were dead code.
