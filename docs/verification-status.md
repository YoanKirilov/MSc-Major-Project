# Current verification index

Updated 27 October 2026. Use this index for current status; dated execution reports
retain the behaviour and results actually verified at their stated revision.
Automated passes are not certification, proof of network safety or a reader study.

## Latest implementation and live verification - 27 October

[Monitoring/evidence/report fixes](rest-fixes-20261027.md) implement F1/F4/F2/F3.
WebKit F5 is deferred at the owner's request. Current normal build matches
`5ef8b4b9ad40e95f807b`, contract 3; Nmap/Ollama ready, storage OK.
Fresh Light completed 10/10 checks; Deep completed 1/1 this-PC check. The explicit
complete-coverage gate passed. Replay reproduced 171 services/11 findings/two
certificate interpretations; 13 ready AI records revalidated with prompt 4.4.1.
Both running refreshes, automatic report opening and four viewport sizes passed.
All 853 normal evidence files stayed unchanged; owned test processes/port closed.

Final offline: 1,008 Python/305 JavaScript passes, five privilege skips; syntax,
lint/208-file formatting, installed wheel and security gates passed. The newly
flagged tooling-only msgpack dependency was patched to 1.2.3, with no ignores.
74 focused Chromium/Firefox cases passed, plus six final prompt-version workflows;
these are not a fresh full matrix or a WebKit pass. Human/real-AT/Ubuntu evaluation
and publication remain separate. No commit, push or hosted rerun was performed.

## Preceding live recheck - 27 October (historical)

[Fresh scans, verification and remaining issues](verification-review-20261027.md).
Normal source/build still match; no restart was performed in this recheck. Light
finished partially (2/6 discovered devices checked); Deep failed (0/1 completed).
Both stopped on `list_timeout` while enumerating local interfaces. Subsequent
local-only interface reads passed; intermittent reliability remains open. Refresh,
saved failed/partial reports, exports, inventory and four viewport checks passed.
Raw replay and four ready AI explanations revalidated. Fresh offline, security and
installed-wheel gates passed. Full Chromium/Firefox: 163 passes each; WebKit:
163 passes plus one intermittent navigation teardown error, so not a green gate.
The linked record includes focused diagnostics and five remaining issues.
All existing normal reports remain unchanged. These outcomes do not rewrite the
preceding successful 26 October pair or turn this pair into a complete scan pass.

## Earlier implementation - 27 October (historical)

[Fixes, CVE policy and verification](fixes-cve-20261027.md) supersede the open
implementation findings below. Current source build is `1b6127342ba5b5601dc3`,
API contract 3. QA/security and a fresh installed wheel use the patched dependency
pins. After the user confirmed no active scans, the normal runtime was updated
and restarted; authenticated readiness confirms the matching build, Nmap/Ollama
ready and storage OK. Hosted run 24 is not updated by local deployment.

CVE research retains separate version and same-product references, including other
or unknown versions, dates and bounded/partial coverage. Actual NVD research of a
saved fingerprint succeeded; no fresh device scan or model generation was started.
All 853 normal evidence files remain unchanged. Use the linked execution record
for recorded failed attempts. Final offline: 1,000 Python/301 JavaScript passes;
full Chromium/WebKit: 163 passes each; Firefox: 162 full-suite passes before final
test-fixture corrections, with final focused recovery passing in all engines.
Reader/real-AT work remains pending.

## Preceding result - 26 October (historical)

[Full review, findings and follow-ups](full-review-20261026.md).

- Normal backend matches source build `2e3a157beed5920419aa`, API contract 3;
  no restart is currently required by the measured public freshness check.
- One fresh Light/home scan and one Deep/this-PC scan completed without scan
  errors. Light checked 6/6 discovered devices; Deep checked 1/1 selected address.
  Both running-refresh checks and automatic report opening passed. Raw replay
  reproduced 111 service records/11 findings; 13 ready AI records revalidated.
- 987 Python/296 JavaScript passes, lint/format/syntax and fresh installed wheel
  passed. Complete browser suites finished: Chromium 157/157, Firefox 157/157;
  WebKit 152 passes/five failures (three focus expectations, two intermittent
  workflow page-error checks). No skipped browser cases. The extra coverage run
  had one timing/output-test failure; focused normal/instrumented reruns passed.
  That failed run is retained and not called a green coverage gate.
- Fresh security gate **failed**: four unique advisories affect locked `filelock`
  and build/dev `setuptools`. Static and secret checks passed. No ignore or
  dependency upgrade was applied to turn the gate green.
- [GitHub run 24](https://github.com/YoanKirilov/MSc-Major-Project/actions/runs/39670678601)
  on local/remote HEAD `a131355` has 15 passing jobs/two failed Windows WebKit jobs.
  The CVE-focus assertion reproduces locally; WebKit now launches with OS security
  unchanged. The full review distinguishes mouse activation from keyboard focus.
- All 853 normal evidence files stayed unchanged. Owned live-test processes and
  port were independently confirmed closed; all 270 source inputs stayed unchanged.
  Pi-hole and real participant/AT/lab
  evaluation remain outside this execution. No commit, push or CI rerun was made.

## Prior verification snapshot - 21 October

The following retains the preceding execution state; it is not current restart,
security, WebKit availability or hosted-CI advice. Use the current result above.

Latest execution: [21 October code organisation and fresh live verification](organisation-live-verification-20261021.md).
Pure scan-start ownership/recovery state is now a separately tested module.
The current offline gate passed 987 Python/296 JavaScript tests; 30 Chromium/Firefox
acceptance cases, security and installed-wheel checks passed. Fresh Deep completed
1/1 selected check with six ready explanations. Fresh Light failed before discovery
completed: the precise reason is an eight-second Windows `adapter_query_timeout`.
Seven AI records revalidated; 853 normal evidence files and 270 source inputs stayed
unchanged. Owned processes/port are closed. The live helper exited 1 because Light
finished before a running-refresh check could be exercised; a complete live pass
is **not** claimed. Normal deployment still needs a task restart.

The [preceding F1-F4 fixes](issue-fixes-20261021.md) remain in place: stale start
outcomes, status-dependent recovery, lost interface reasons and interrupted-search
wording are fixed. Windows fresh-query reliability remains separate open work.

The [preceding 21 October live review](live-review-20261021.md) remains unchanged:
Deep completed 1/1 this-PC check and Light stopped during discovery. Seven ready
AI records revalidated. That Light failure is not retrospectively marked successful,
and its exact underlying interface-query cause was not recoverable from the old reason.

Latest implementation: [20-21 October fixes and acceptance evidence](findings-implementation-20261020.md).
The preceding review's trust update, uncertain scan-start recovery and build-check
gaps are fixed locally. All three project environments now use pip 26.2.2 and
standalone/vendored certifi 2026.10.19. The updated complete dependency/static/secret
gate passed. This does not rewrite the [preceding review's failed gate](live-review-20261020.md).

The [19 October implementation](post-review-implementation-20261019.md) retains its
retry/CVE/DNS fixes, bounded cross-tab receipts and naming/build diagnostics. The
normal app still runs build `3e5d3881e53f804e688b` and API contract 2, which predate
the newest fixes. Finish active work, restart the task, reopen its session link and
reload tabs for API contract 3. Actual reader/AT evaluation and publication remain pending.

## Revision and release status

- Published baseline: `b49c71a66fec4a61b3f2be11e3565b50480b1265`.
  [GitHub run 23](https://github.com/YoanKirilov/MSc-Major-Project/actions/runs/39079432854)
  was recorded green for its twelve platform/browser jobs and security job in
  [the live review](live-review-20261018.md). No newer hosted result is asserted.
- Local HEAD observed during the latest execution: `a131355`, with later documentation
  changes. No commit, push or CI action was performed by that execution. No newer
  hosted result was checked; the baseline run does not verify the current source.
  Named test/build artifact folders identify local executions, not published releases.
- The normal backend matched during the 20 October review but now predates these
  changes. The helper correctly reports `restart_required: true` by comparing the
  actual source build/contract, not matching static assets. No normal restart was
  performed. Installed-package and isolated-backend passes are not deployment.

## Evidence by type

Latest offline gate: **987 Python, 296 JavaScript**, 30 syntax checks, lint and
204-file formatting passed; five Windows privilege skips, 159 opt-in cases deselected.
The [latest execution](organisation-live-verification-20261021.md) records 30 actual
Chromium/Firefox acceptance cases, security and installed-wheel passes. Deep completed;
Light's Windows-query timeout remains unresolved, and both-running refresh was not
exercised. See that record for the failed live-helper gate and cleanup evidence.
The [preceding 21 October review](live-review-20261021.md) records 16 focused actual Chromium/
Firefox cases and new security/installed-wheel passes. Its fresh Light scan was
interrupted during discovery; Deep completed 1/1 check with 14 open features/five
review items. Raw replay reproduced 21 Deep service records and all five findings;
seven ready explanation records revalidated across both reports. Exactly two scans
were submitted; refresh/export/inventory/viewport checks passed. All 853 protected
normal files and the 267-file source/test/script/lock/workflow manifest stayed
unchanged. The owned backend and port were independently confirmed stopped.
The earlier [saved-only reopening](findings-implementation-20261020.md) remains
separate evidence; it must not be relabelled as a fresh scan or model-generation test.

| Type | Latest record | What it does not establish |
| --- | --- | --- |
| Offline Python/JavaScript/lint | [21 October organisation](organisation-live-verification-20261021.md) | Actual model output or a live scan |
| Synthetic real-browser checks | [21 October organisation](organisation-live-verification-20261021.md) | A new hosted matrix or real assistive-technology use |
| Dependency/static/secret audit | [21 October organisation](organisation-live-verification-20261021.md) | Certification, OS trust updates or a hosted pass |
| Installed wheel/dependencies | [21 October organisation](organisation-live-verification-20261021.md) | Production deployment or an authorised Ubuntu live lab |
| Actual authorised Light/Deep scans | [21 October organisation](organisation-live-verification-20261021.md) | A Light pass or both-running refresh: not established; remote exposure from a self-scan |
| Saved Light/Deep reopening | [21 October issue fixes](issue-fixes-20261021.md) | A fresh network scan, host retry or explanation generation |
| Model generation and wording audit | [21 October organisation](organisation-live-verification-20261021.md) | Every sentence being model-authored or understood by novices |
| Hosted platform/browser baseline | Run 23 above | Current source passing a newer hosted CI run |
| Reader/assistive-technology/reference lab | [Evaluation plan](evaluation.md) | Participant or physical-device results: these remain pending |

Model readiness means that the installed service/model answers its health check;
it is not a generation test. AI-selected wording may still fall back to reviewed
fixed guidance. Source/fallback metadata stays available in Supporting information;
there is no report-page AI-outage banner or manual wording-retry button.

The critical CVE, library and workflow fixtures now select the actual configured
engine; focused local Chromium/Firefox execution is recorded separately from the
older hosted baseline. State the fixture/engine in evaluation claims. Local Windows
WebKit remains OS-blocked; no security protection
was disabled to obtain a pass. A hosted synthetic Ubuntu pass is not a live Ubuntu
lab evaluation. See [the remaining recommendations](follow-up-audit-20261018.md).

## Earlier baseline records

[28 September quality baseline](quality-evidence-20260928.md),
[18 October response/CVE fixes](remaining-fixes-20261018.md),
[follow-up audit](follow-up-audit-20261018.md), and
[test history](testing.md). Later successful runs do not erase earlier failures.
Private test artifacts, report text, raw XML, session links and screenshots must not
be published as ordinary CI artifacts or dissertation appendices without review.
