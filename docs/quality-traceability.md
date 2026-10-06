# Quality requirements and verification links

Baseline established before the quality-plan live run on 28 September 2026.
Acceptance thresholds are in [quality-plan.md](quality-plan.md), not implied by test names.
Current execution: [quality-evidence-20260928.md](quality-evidence-20260928.md).
PASS/LIMITED/FAIL/PENDING apply to the stated test conditions, not a whole ISO standard.

## Follow-up evidence - 29 September 2026

The table below preserves the 28 September baseline. Later evidence is recorded in
[testing](testing.md) and [release checks](release-checks.md):

- Q03/Q06/Q11: responsive/browser regressions, explicit counts and stable ordering.
- Q04: copied real-report recovery drill passed without changing source evidence;
  an older checkpoint remains honestly incomplete.
- Q08/Q14: local dependency, static-analysis and secret gates passed. Remote enforcement,
  independent review, release approval and reproducible-build work remain open.
- Q07: improved presentation is implemented, but real comprehension results remain pending.
- Q10/Q12: local package/browser checks do not replace actual Pi-hole/Ubuntu evaluation.

## Original baseline

Current follow-up — 6 October 2026: Q03/Q04/Q06/Q08/Q11 are covered by
`tests/unit/test_review_fixes.py`, `tests/notes_ui.test.mjs` and the expanded
two-tab `tests/browser_test_library.py`. They verify full-snapshot note adoption,
storage fault/retry boundaries and unchanged evidence. Q05 covers unique five-job
admission, cancellation and AI queue expiry. Q07/Q13 add reviewed service/role
labels, specific comparison limits and user-owned checklist progress; actual human
comprehension remains pending. `scripts/benchmark_history.py` measures Q05/Q11
JSON search behaviour in synthetic libraries. Exact execution evidence belongs in
`fixes-and-improvements-20261006.md`; the original table below remains historical.

| ID | Required behaviour | Main implementation | Automated verification | New baseline status |
| --- | --- | --- | --- | --- |
| Q01 | Scan only authorised targets; preserve missing coverage | `app/security/scope.py`, `app/api/scans.py`, `app/jobs/supervisor.py` | `tests/unit/test_scope.py`, `tests/unit/test_supervisor.py`, `tests/unit/test_improvements.py` | PASS tested scope: home preflight and negative tests; one unreachable device remains unchecked |
| Q02 | Findings trace to retained observations | `app/scanner/parser.py`, `app/risk/engine.py` | `tests/unit/test_nmap_parser.py`, `tests/unit/test_rules.py`; live retained-XML replay | PASS consistency: 13 host results and 8 findings replayed; lab accuracy remains pending |
| Q03 | Refresh/retry recover the job without duplicate scanning | `app/static/js/dashboard.js`, `app/jobs/supervisor.py` | `tests/dashboard_ui.test.mjs`, `tests/browser_test_workflow.py` | PASS synthetic in-progress/browser regressions and actual finished-report refresh |
| Q04 | Bounded, recoverable JSON storage; historical reports unchanged | `app/storage/` | `tests/unit/test_storage.py`, `test_instance.py`, `test_maintenance.py`, `test_improvements.py`; pre/post hashes | PASS tested faults/recovery and 34 unchanged readable reports; operational backup drill pending |
| Q05 | Work queues and time/output limits stay bounded | `app/scanner/runner.py`, `app/jobs/supervisor.py`, `app/explanations/service.py` | `tests/unit/test_process_runner.py`, `test_commands.py`, `test_supervisor.py`; live elapsed time | PASS bounds regressions; 255-second live sample, 194,345-byte report; no load/percentile claim |
| Q06 | App startup and Run again have usable recovery/setup | `app/static/js/api.js`, `dashboard.js`, `scan.js`, templates | `tests/api_ui.test.mjs`, `dashboard_ui.test.mjs`, `report_ui.test.mjs`, `tests/browser_test_workflow.py` | PASS startup/Light/Deep navigation regressions; no overflow in actual desktop/mobile views |
| Q07 | Users understand observations/limits/first actions | `app/explanations/presentation.py`, report UI | `tests/report_ui.test.mjs`; `docs/evaluation-session.md` and real participant scoring | LIMITED: assistant readability review only; count/mobile issues planned, participant study PENDING |
| Q08 | Authentication, CSRF, scope and secret boundaries hold | `app/security/`, `app/config.py`, Pi-hole connector | `tests/unit/test_session.py`, `test_scope.py`, `test_pihole_setup.py` | LIMITED: negative tests passed; independent security/dependency/secret review pending |
| Q09 | AI wording remains factual; provenance and fallback are honest | `app/explanations/`, `app/static/js/report.mjs` | `tests/unit/test_explanations.py`, `test_partial_wording.py`, `test_improvements.py`; real-model record validation | PASS tested contract: 9 ready real-model records, no rejected fields; outage/retry covered synthetically |
| Q10 | Packaged app and external integrations behave as documented | `app/main.py`, `app/scanner/pihole.py`, package config | `tests/integration_test_dashboard.py`, `tests/unit/test_pihole.py`, `scripts/check_package.py` | LIMITED: fresh wheel/browser/Nmap/Ollama passed; actual Pi-hole unavailable |
| Q11 | Maintainable boundaries; no unreferenced shipped modules/assets | `app/`, `scripts/`, package configuration | Ruff; `tests/unit/test_layout.py`; static asset traversal | PASS defined checks and organisation review; no unused shipped file found; not proof every function is used |
| Q12 | Explicitly tested platform/install and schema compatibility | `app/config.py`, `app/storage/`, workflow | `tests/unit/test_dependency_locks.py`, `test_config.py`, `test_storage.py`; installed-wheel/CI matrix | LIMITED: Windows/Python 3.14.2 and 34 reports passed; remote Ubuntu/matrix not verified |
| Q13 | Names/advertisements do not imply identity or safety | `app/scanner/names.py`, `mdns.py`, `app/profiling/` | `tests/unit/test_name_reliability.py`, `test_mdns.py`, `test_classifier.py`; real naming-source review | PASS tested provenance: 3 current names, no conflicts; identity not independently proven |
| Q14 | Release can be traced and security checks reviewed | Git, locks, `.github/workflows/checks.yml` | Source manifest, package hash; independent review and dependency/secret audit to add | LIMITED: source/wheel fingerprints saved; release, remote protections, security audit/SBOM pending |

For each later change, cite affected Q IDs in the change record/PR and name the
regression test. Keep prior dated evidence; do not overwrite failure histories.
