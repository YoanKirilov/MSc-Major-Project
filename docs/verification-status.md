# Current verification index

Updated 21 October 2026. Use this index for current status; dated execution reports
retain the behaviour and results actually verified at their stated revision.
Automated passes are not certification, proof of network safety or a reader study.

Latest implementation: [21 October F1-F4 fixes and acceptance evidence](issue-fixes-20261021.md).
Stale start outcomes, status-dependent recovery, lost interface reasons and
interrupted-search wording are fixed locally. The current offline gate passed
987 Python/292 JavaScript tests; 14 focused and 16 parallel-workflow real-engine
browser cases passed (30 total across Chromium/Firefox).
Security, installed-wheel and saved-report rechecks passed; the normal backend
still needs a task restart. No new network scan or model generation was submitted.

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
- Current source: that baseline plus uncommitted local fixes/improvements. No new commit, push
  or CI run was created by this work. The baseline run does not verify
  this working tree. Named test/build artifact folders identify local executions,
  not published releases.
- The normal backend matched during the 20 October review but now predates these
  changes. The helper correctly reports `restart_required: true` by comparing the
  actual source build/contract, not matching static assets. No normal restart was
  performed. Installed-package and isolated-backend passes are not deployment.

## Evidence by type

Latest offline gate: **987 Python, 292 JavaScript**, 29 syntax checks, lint and
204-file formatting passed; five Windows privilege skips, 159 opt-in cases deselected.
The [21 October review](live-review-20261021.md) records 16 focused actual Chromium/
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
| Offline Python/JavaScript/lint | [21 October issue fixes](issue-fixes-20261021.md) | Actual model output or a live scan |
| Synthetic real-browser checks | [21 October issue fixes](issue-fixes-20261021.md) | A new hosted matrix or real assistive-technology use |
| Dependency/static/secret audit | [21 October issue fixes](issue-fixes-20261021.md) | Certification, OS trust updates or a hosted pass |
| Installed wheel/dependencies | [21 October issue fixes](issue-fixes-20261021.md) | Production deployment or an authorised Ubuntu live lab |
| Actual authorised Light/Deep scans | [21 October review](live-review-20261021.md) | A Light pass: it was interrupted; or remote exposure from a self-scan |
| Saved Light/Deep reopening | [21 October issue fixes](issue-fixes-20261021.md) | A fresh network scan, host retry or explanation generation |
| Model generation and wording audit | [21 October review](live-review-20261021.md) | Every sentence being model-authored or understood by novices |
| Hosted platform/browser baseline | Run 23 above | Current unpublished changes passing hosted CI |
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
