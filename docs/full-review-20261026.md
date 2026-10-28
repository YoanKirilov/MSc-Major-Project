# Full software and live review - 26 October 2026

Status: checks complete; **not all gates passed**. This record separates actual scans, synthetic
feature tests, installed-package checks and hosted CI. A test pass is not proof
that every device is safe or that every person understands the report.

## Scope and preservation

- Local HEAD `a131355e7ac17ad3ebc7b7a8d90cbd65b3d4aa14`; prior documentation edits
  were preserved. No commit, push, CI rerun or notification change is authorised
  by this read/check request or performed here.
- Source build `2e3a157beed5920419aa`, API contract 3. The normal app now matches;
  its public build check reports `restart_required: false` and no asset mismatches.
- Fresh local adapter/default-route facts matched the previously authorised home
  range and this-PC target. One Light/home and one Deep/this-PC scan were started
  in `.test-artifacts/live-review-20261026/data/`, with Pi-hole disabled. No other
  target or network was added. Source was frozen with a 270-file hash manifest.
- Normal reports/settings/labels are not used for destructive tests. Report
  deletion/Undo, settings changes, recovery and backup checks use synthetic stores.

## Confirmed findings so far

### F1. Current security gate fails: newly detected dependency advisories

Fresh audit `.test-artifacts/security-48299b34d0/` exited 1. The application/dev
graph has four advisories across two packages; the security-tool graph has three
across one package. Counts overlap: these are four unique advisories, not seven
independent vulnerabilities in the application. Static analysis remains 16 low,
zero medium/high findings; secret detection found zero potential secrets.

| Locked package | Finding | Published patched version |
| --- | --- | --- |
| `filelock` 3.32.7 (application/dev), 4.0.5 (security tooling) | [CVE-2026-112940](https://github.com/advisories/GHSA-v4x8-3wr5-3wq8): reader/writer-lock SQLite path/side-file handling | 4.2.1 |
| Same versions | [CVE-2026-112913](https://github.com/advisories/GHSA-9vhv-jxww-xfm5): Windows reader/writer-lock SQLite side files | 4.2.1 |
| Same versions | [CVE-2026-112907](https://github.com/advisories/GHSA-567q-5qvw-pf92): Windows soft-lock marker can block acquisition past its timeout | 4.2.1 |
| `setuptools` 84.0.0 (dev/build locks) | [GHSA-xmj3-9gf7-h52w](https://github.com/advisories/GHSA-xmj3-9gf7-h52w): Windows legacy wheel-install path escape | 84.1.0 |

Applicability is narrower than package presence: this app imports `FileLock`, not
the SQLite reader/writer classes, and the runtime resolves it to
`filelock._windows.WindowsFileLock`, not the soft-lock path. This observation is
not a vulnerability exemption or proof of safety on every supported platform.
No malicious wheel/lock exploit was attempted. Package installation success does
not clear the advisory gate. The current `filelock<4.0` project bound prevents
simply selecting the published 4.2.1 fix; a deliberate compatibility/lock update
and runtime/QA/security environment verification are required. No ignores,
automatic upgrades or running-environment changes were made during this review.
The advisories were published on 17/19 October and updated on 23 October; the
fresh audit result supersedes the older clean audit, not its historical record.

### F2. GitHub run 24: CVE focus expectation fails on Windows WebKit

[Run 24](https://github.com/YoanKirilov/MSc-Major-Project/actions/runs/39670678601)
on the current HEAD failed. Of 17 jobs, 15 passed (four offline/package jobs,
security, ten browser jobs). Both Windows WebKit jobs failed in
`tests/browser_test_cves.py:201`, expecting **Check CVEs again** to be focused
after mouse-activating **Reload saved CVE references**. Dependency installation
and WebKit launch succeeded; this is not a browser-download or suite timeout.

The exact `[webkit-True-True]` case failed locally too:
`.test-artifacts/webkit-cve-20261026.xml`. Unlike the earlier environment, WebKit
now launches locally with OS protections unchanged. The current failure must not
be described as an OS-blocked browser or fixed by dropping WebKit from CI.

A private two-modality diagnostic reused the original case without altering the
app or its acceptance assertions. Pointer activation left the reload control
unfocused and reproduced the assertion; explicit focus + Enter activation passed
the entire original case, including GET-only receipt recovery and reference links.
Evidence: `.test-artifacts/cve-focus-probe-20261026/results.xml` (two diagnostic
cases; the pointer case expects the original failure, so these are **not two new
passing product acceptance cases**).

The code only transfers focus when the reload control had focus and focus has not
moved elsewhere. The evidence supports an input-modality mismatch in the test,
not lost CVE data or failed recovery. Recommended follow-up: separate pointer
behaviour from actual keyboard-focus restoration; keep a real focus assertion for
keyboard activation and ensure a user moving elsewhere is not refocused. Do not
delete the accessibility assertion or mark the hosted run green without verification.

The complete local WebKit suite subsequently reached all 157 cases: **152 passed,
five failed**. Three failures are focus expectations: both lost-CVE-response cases
at line 201 and the library name-refresh case at `browser_test_library.py:296`.
The latter explicitly focuses and then mouse-clicks the button; it is not a pure
keyboard interaction. A private diagnostic using Enter for name refresh passed
that assertion, then exposed the same mouse-focus expectation for its CVE control
at line 322. Using Enter for **both** controls passed the entire original library
case, with every acceptance assertion retained. Native confirm focus remained on
the name-refresh control before/after each dialog. This does not support disabling
native confirmation or weakening keyboard focus restoration.

Evidence: `.test-artifacts/webkit-trace-20261026/results.xml`,
`keyboard-actions-results.xml` and `trace-summary.json`. Private diagnostic passes
do not turn the original full-suite failures into passes. No product/test change
or GitHub rerun was made; the hosted run remains red.

### F3. Names unavailable in this Light result; timeout, not "no name exists"

All six Light PTR lookups timed out at approximately 2.0 seconds; no mDNS
observations were recorded. Deep separately obtained this PC's reverse-DNS name
in 434 ms. These are different target sets, so this does not prove that the same
device changed names between profiles. The app correctly displayed unnamed
devices rather than inventing names or treating a manufacturer as an identity.

One extra read-only lookup for an already scanned unnamed address, with a
diagnostic-only five-second limit, still timed out at 5.012 seconds. Application
settings and the normal two-second budget were unchanged. Increasing every lookup
deadline is therefore not demonstrated to solve this result. Investigate resolver/
router PTR availability and optional per-source diagnostics; retain bounded,
explicit targeted name retries and user nicknames. Do not promise every device
will advertise a name or reintroduce Pi-hole as a required dependency.

### F4. Two WebKit workflow page-error checks fail intermittently

The complete WebKit run also failed the final `assert not errors` in:

- `test_light_and_deep_tabs_are_independent[webkit-viewport0-False]` (line 219).
- `test_scan_ai_wait_failure_retry_history_and_known_host_rescan[webkit]` (line 518).

Both recorded a progress-request message ending **due to access control checks**.
Their preceding assertions for scan independence, cancellation, saved results,
analysis wait/retry/navigation and session handling completed before the final
error assertion. This is not evidence that a real scan failed or that CORS should
be opened up. The actual live pair passed in Chromium; that does not clear WebKit.

Two private traced executions of these original cases passed without the progress
access-control message. The trace did observe navigation-cancelled module requests
and the original intentionally broken-module error expected by its test. Timings
can change under instrumentation: neither a definite cause nor resolution is
established. Preserve the full-suite failures. Follow up with request/navigation/
unload timing, retired-page polling and deterministic readiness/cancellation tests;
do not globally ignore `pageerror`, filter every access-control message, relax
session/CSRF/CORS protections or merely add arbitrary sleeps.

### F5. Instrumented subprocess-output test fails under concurrent test load

The extra coverage execution had **986 Python passes, one failure, five skips**:
`test_timeout_with_inherited_pipes_preserves_partial_output` expected a marker but
captured empty stdout. Its one-second execution budget includes Python startup and
spawning a descendant. The normal full offline suite passed this case. A focused
rerun without coverage passed, and one focused rerun with coverage passed too.

This does not establish instrumentation alone as the cause or prove a production
output-loss bug. A startup/deadline assumption and a delivery/cleanup race must be
distinguished with explicit ready/output events. Do not extend real scan deadlines
or accept dropped evidence to silence the assertion. The failed instrumented run
is retained separately from the normal offline pass and the focused passes.

The instrumented baseline measured **90.05% statement coverage**, **80.69% branch
coverage** (87.66% combined) over application Python. It is not a green coverage
gate, JavaScript coverage or proof that every behaviour is tested. Prioritise
CLI/maintenance, network-failure and API/error branches rather than an arbitrary
percentage. Artifacts: `.test-artifacts/coverage-20261026/`,
`runner-focused-20261026.xml` and `runner-cov-focused-20261026/`.

### I1. Related CVE references are valid research leads but poorly prioritised

One read-only actual NVD lookup used a saved `lighttpd:1.4.67` fingerprint, sending
no device names/addresses/MACs/report. It resolved the exact product dictionary
entry and returned zero version-specific matches, plus 35 related product records.
The five returned research leads have CVE identifiers from 2005-2007. No annotation/report was
changed. Evidence: `nvd-provider-check.json` in the private live folder.

The current bounded implementation reads the first product-result page and keeps
the first five qualifying entries. Their being related to the product is not
proof of relevance to the detected version. Improve relevance/recency selection
with bounded pagination and tests, retain publication/update dates as well as
truncation/unknown applicability,
and retain the clear distinction between version candidates and related research.
Do not label those old records as vulnerabilities confirmed on the device or
interpret zero exact matches as safety. Real GET/provider behaviour and synthetic
UI/storage behaviour are separate checks, not an asserted live annotation round-trip.

## Completed checks

- Full offline gate `.test-artifacts/checks-abe23b5aee/`: 987 Python passes,
  five Windows privilege skips and 159 opt-in deselections; 296 JavaScript passes,
  30 syntax checks, lint and 204-file Python formatting passed. Application import
  reachability and shipped template/asset reachability passed: no proven-unused
  application files were identified for deletion.
- Fresh offline installed wheel `.test-artifacts/package-f7ae7beb41/`: seven
  pages, 32 assets, synthetic create/reopen/delete/Undo and dependency consistency
  passed. This used the existing trusted wheelhouse, not an upgrade or security pass.
- Complete real-engine synthetic browser suites (471 selected cases total):

  | Engine | Passed | Failed | Skipped | Artifact folder |
  | --- | --- | --- | --- | --- |
  | Chromium | 157 | 0 | 0 | `.test-artifacts/checks-9ae14d48af/` |
  | Firefox | 157 | 0 | 0 | `.test-artifacts/checks-aabd652bbf/` |
  | WebKit | 152 | 5 | 0 | `.test-artifacts/checks-8e60acb9cd/` |

  There were 994 non-browser deselections in each browser-only execution, not
  skipped browser cases. The five WebKit failures are detailed in F2/F4; private
  diagnostics are not added to these acceptance totals. Concurrent suite durations
  were approximately 19m45s/30m23s/20m56s respectively; these are not app-performance
  benchmarks. Every suite finished; no fail-fast cutoff hid subsequent cases.

## Architecture and organisation

The single FastAPI instance owns its JSON root before recovery; separate scan IDs,
short per-document locks and independent annotation/label files support concurrent
jobs without two servers writing that root. Scope/current-connection verification
stays fail-closed. Model wording is a bounded post-scan stage, not a replacement for
raw evidence or the rule-derived priorities. Public NVD research remains an explicit
software-fingerprint lookup, never an inference that an open port proves a CVE.

Application-module and asset reachability tests passed. The existing separation
between API, schemas, workers, scanners, storage, validation and frontend state is
useful; no proven orphan justifies deleting files or dropping compatibility imports.
No source was reorganised during frozen live execution. Avoid a wholesale rewrite
to Flask, a new database, or reformatting unrelated user changes as "cleanup".

Maintainability follow-up: `scan.js` is about 75 KB and `jobs/supervisor.py` about
49 KB. Extract one cohesive report interaction/controller or worker phase at a
time behind existing acceptance tests. Size is a review signal, not evidence of a
bug or a reason to fragment every function. Current verification navigation will
be updated separately from retaining dated execution history.

The GitHub `main` branch was independently read and matches local HEAD. Its complete
406-entry tree contains no `.test-artifacts`, virtual environment, session-secret,
runtime scan/settings/nickname JSON or Pi-hole password paths in the checked path
patterns. This path check and the local secret scan do not constitute a complete
secret-history audit. No remote write or CI rerun was performed.

### I2. Novice-reader UX needs evaluation, not more technical controls

The live overview is materially clearer than the raw results: it defines a
feature with web-page/file-sharing examples, separates review items from confirmed
problems and explains self-scan limits. The actual Deep next step names Windows
Security and warns against disabling the firewall/core services. Preserve these.

Remaining wording is repetitive: several informational items say essentially
"a connection answered; check its purpose". Consider a concise grouped summary
with every underlying observation still reachable, rather than another top-level
filter or extra alarming cards. Explain HTTP/encryption/redirect at the point of
use, with a concrete next action; do not claim unidentified features were assessed.
Model-field provenance shows mixed generated/reviewed wording, so successful model
generation is not a claim that every field was rewritten or everyone understands it.

Use a small nontechnical-reader study to check whether someone can identify which
device to review, understand an unknown result and choose a safe next step. Native
keyboard/focus semantics and comfortable touch targets must survive any compacting.
Reference principles: [unusual words](https://www.w3.org/WAI/WCAG22/Understanding/unusual-words.html),
[focus order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html), and
[minimum target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
These references guide improvements; automated tests do not establish conformance
or substitute for disabled-reader/assistive-technology evaluation.

## Limits

Pi-hole installation, real
assistive-technology/participant studies, remote-exposure confirmation and a new
hosted CI pass are outside this execution; none is inferred from simulation.

## Actual live results and evidence

| Profile | Coverage | Open features | Findings | Analysis |
| --- | --- | --- | --- | --- |
| Light | Discovery completed; 6/6 discovered device checks finished | 10 | 3 low, 4 informational | 8 ready records |
| Deep / this PC | 1/1 selected address check finished | 14 | 4 informational | 5 ready records |

Light finished in about 289 seconds, Deep in 541 seconds. Neither recorded scan
errors. Light had no warnings; Deep correctly warns that a local self-scan does
not establish another device's or the internet's access through the firewall.
These are observed features and selected-check results, not confirmed exploits.
Device presence can vary between runs; this is not an exhaustive inventory promise.

The real helper exited **0** (`LIVE_SCAN_PAIR_COMPLETE`). Exactly two scan-start
submissions were recorded; both jobs survived refresh while running, reports opened
automatically after analysis, and no page errors were recorded. Layouts passed at
320/390/768/1,440 pixels; mobile overview/device-card screenshots were inspected.
Two private exports, inventory filtering/reset and report return context passed.

The read-only audit reproduced all **111 service records** (90 Light, 21 Deep)
and **11 findings**, with no missing completed-host raw files. One Light certificate
date interpretation revalidated. All **13 explanation records** revalidated;
identifier-free selected model inputs, zero rejected fields, zero fallback reasons.
This verifies selected facts/wording constraints, not universal comprehension or
every output field being model-authored. The displayed overview defines a feature
with familiar examples; self-scan limitations and safe next steps remain explicit.
Terms such as HTTP/encryption/redirect and repetition still warrant novice-reader
evaluation before making claims that everybody understands the result.

All **853** protected normal evidence files stayed unchanged. Owned wrapper PID
23804 and server PID 2960 were independently absent after cleanup; owned port
33132 was not listening. No normal process was stopped. The previous eight-second
Windows-query failure did not recur here; this successful run is not proof its
intermittent cause has been fixed. No such fix or deadline change was made.
After all suites and diagnostics finished, the **270-file** source/test/script/
lock/workflow manifest still matched; the independent normal-store rehash showed
zero changed/missing protected files and zero new normal files. Whitespace checks
passed. Documentation navigation now leads to this current record, and stale
restart/OS-blocked/clean-security statements are explicitly historical. No
application refactor or removal was required; previous user edits were preserved.

## Feature verification map

All synthetic references below point to the available unit/integration/browser
suites. Final per-engine outcomes must be read alongside this map; it is not an
assertion that every row passed in every engine or every physical environment.

| Area | Executed evidence / boundary |
| --- | --- |
| Start/readiness/scope/refresh | Actual home pair and current build check; synthetic stale/lost replies, GET-only recovery, authentication and changed-network cases |
| Concurrency/cancellation/queue | Two actual concurrent scans; synthetic five-job admission, queue budgets, cancellation and shutdown/recovery tests, not five extra live scans |
| Nmap/profiles/raw coverage | Both actual profiles; completed-host XML replay and parser/unit checks; no extra arbitrary Deep targets |
| Names/classification | Actual PTR diagnostics and one name found in Deep; no mDNS advertisements observed; one bounded extra DNS diagnostic; no invented names |
| AI simplification | Actual local model generation plus replay; synthetic outage, batch, privacy, validation and finite-deadline cases |
| CVE research | One actual NVD software-fingerprint lookup; synthetic links/exact-vs-related/receipt/cache/GET recovery; WebKit focus failures remain explicit; no live report annotation written |
| Devices/nicknames/favourites | Actual inventory display/filter/reset/return context; synthetic edits, identity safeguards, lost responses and cross-tab cases |
| Report history/search/paging | Synthetic 24-row pages, filtering, scroll/reflow and navigation; existing household history not edited |
| Delete/bulk delete/Undo | Synthetic API/browser and fresh installed-package checks; no household report deleted |
| Tasks/report titles/annotations | Synthetic persistence, conflict/lost reply, checklist/search/focus cases; no real review marked done or fixed |
| Export/privacy/supporting info | Two actual private previews and synthetic redaction/overflow/focus/return-context tests; not an anonymity guarantee or physical print evaluation |
| Settings/themes/accessibility | Synthetic engine-specific keyboard, contrast, text-spacing, larger-text and responsive cases; not a real screen-reader/disabled-user study |
| Storage/backup/restore/retention | Isolated unit/integration stores; write/read limits, atomic writes, corruption/recovery, backup/restore and ownership tests; no household migration/pruning |
| Session/CSRF/headers/dependencies | Synthetic session/request/header checks and static/secret audit; dependency gate failed and is not waived |
| Installation | Fresh offline installed wheel: seven pages/32 assets and synthetic report lifecycle; not a new Ubuntu live deployment |
| Pi-hole | Disabled for live work; optional-client code tests are not installation or extraction from a real Pi-hole server |

## Follow-up execution order

1. **Dependency remediation:** verify `filelock` 4.2.1 compatibility, revise the
   current `<4.0` project constraint deliberately, reconcile runtime/dev/build/
   security locks, and verify their separate environments. Update `setuptools`
   to the published patched version. Re-run audits, ownership/locking/concurrency,
   full offline tests and a clean installed wheel. Do not disable advisory checks.
2. **Correct the focus acceptance scenarios:** exercise real keyboard activation
   for CVE/name restoration, preserve every data/receipt/state assertion and add
   pointer and moved-focus cases separately. Re-run the complete three-engine
   suite, not only the first GitHub failure. Do not force focus onto users who moved.
3. **Resolve the intermittent WebKit workflow errors:** collect deterministic
   request/unload timing, fix the relevant lifecycle or fixture readiness issue
   with a reproducer, retain all page-error assertions, and verify without broad
   error filters or weakened browser/server protections.
4. **Stabilise the output-timeout reproducer:** distinguish child startup from
   buffered-output delivery with explicit ready/output events; retain bounded
   process cleanup and evidence. Re-run normal and instrumented suites and measure
   coverage again. Do not present the initial failed coverage run as green.
5. **Improve naming and CVE usefulness:** diagnose PTR availability before tuning
   budgets; preserve source/confidence and explicit name retries. Improve bounded
   CVE research relevance and retain publication/update/truncation metadata. Keep
   unknown, related and confirmed applicability separate; never infer a CVE from a port.
6. **Evaluate plain language, then small refactors:** test task comprehension with
   nontechnical/disabled readers; reduce repeated informational text and explain
   jargon. Extract cohesive controller/worker phases only with regression evidence.

These are proposed follow-ups, not implemented fixes. Publishing/re-running GitHub
requires a later authorised change; simply re-running unchanged run 24 would not
correct its focus assertions, and a fresh security audit now has additional blockers.
