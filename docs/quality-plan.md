# Software quality management plan

Version 1.0, established 28 September 2026, before the new quality-baseline live scan.
Scope: NetGuard's local, single-user research prototype. Owner: project author.
Status: executable project plan; independent review and release approval pending.

## 1. Basis and limits

Use [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) as the product-quality
reference model, [NIST SP 800-218 SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final)
for selected secure-development practices, and
[ISO 9001](https://www.iso.org/standard/9001) for a quality-management approach based
on objectives, evidence, review and corrective action. ISO's current public overview
identifies ISO 9001:2026; this plan does not assert compliance with that edition or its
predecessor. Check the university's required edition before an academic clause mapping.

This is a tailored, standards-informed plan, not a complete implementation of any
standard, an independent audit, security certification or an ISO-certified management
system. Public standard summaries and the public SSDF are the basis; licensed ISO
requirements have not been assessed clause by clause. Numerical targets below are
project decisions, not thresholds prescribed by ISO/NIST. Do not describe them as such.

Primary outcome: nontechnical users can distinguish observations, limitations and
appropriate next steps without interpreting a scan as proof of safety or compromise.
JSON storage and FastAPI stay in scope. No framework/database migration is required.

## 2. Roles, authority and review cycle

- Project author: approves scope, requirements, risk acceptance and any release.
- Implementation/test assistant: proposes changes, runs authorised checks, records
  commands/results/failures. Assistant self-review is not independent approval.
- Independent reviewer: a supervisor or nominated peer, not yet assigned; reviews
  security-sensitive changes, conclusions and a sample of comprehension scoring.
- Study facilitator/participants: only after required university consent/ethics review.
  No recruitment, personal data collection or participant answers are implied by this plan.

For each change: define the requirement and risk, add a regression where possible,
implement the smallest appropriate change, run checks, update evidence and seek review.
Review open risks weekly and before a release; recheck dependencies before each release
and after a relevant advisory. The author may revise criteria prospectively with a
dated reason, never silently after seeing a failed result.

## 3. Measurable product-quality objectives

Use [the traceability matrix](quality-traceability.md) to connect each objective to
code, named tests and evidence. The coverage below selects project-relevant concerns;
it is not an exhaustive ISO subcharacteristic assessment.

| Concern | Requirement IDs | Project acceptance criterion |
| --- | --- | --- |
| Functional suitability | Q01, Q02 | Every reported service/finding in a retained-evidence replay matches saved source facts/rule output, excluding generated timestamps. Lab detection accuracy requires independently configured ground truth, not replay alone. |
| Reliability | Q03, Q04 | Refresh never starts a duplicate scan; failure/cancellation remains visible. Injected lock/size/write failures leave prior evidence readable; no forced lock bypass. |
| Performance efficiency | Q05 | Two host processes maximum; host-stage budget 30 minutes; AI budget 15 minutes including queue. Collect real duration and file size; investigate Light runs over 10 minutes, but do not mislabel honest timeouts as passed checks. No percentile claim from one run. |
| Interaction capability | Q06, Q07 | Startup failure provides recovery; Run again requires a deliberate Scan click; no desktop/mobile page overflow in tested views. Participant target: at least 80% correct observations, limitations and next-action answers, and zero responses asserting proven safety/compromise. Report sample size and every unsafe interpretation; targets remain unevaluated until a study. |
| Security | Q08, Q09 | Negative session/CSRF/scope tests pass; selected AI inputs omit raw XML, IP/MAC addresses and hostnames; generated text cannot alter factual severity/actions. No unresolved confirmed critical/high software vulnerability may be accepted for a release. |
| Compatibility | Q10 | Real browser workflow and installed-wheel checks pass. Verify Pi-hole against an actual v6 instance before claiming compatibility in deployment. |
| Maintainability | Q11 | Lint, formatting, import/asset reachability and regression checks pass. Review oversized multi-responsibility modules; line count alone does not justify a rewrite or deletion. |
| Flexibility | Q12 | Fresh Windows and intended Ubuntu installations pass the defined matrix; historical schema-v1 reports load unchanged. Untested OS/version combinations remain unverified. |
| Safety | Q01, Q07, Q13 | Scope requires authorisation; no exploits, password guessing or broad packet capture; unknown coverage and identity stay unknown; advice must not encourage HTTP credential entry or bypassing TLS warnings. No safety-critical use is supported. |

Additional AI criterion (Q09): every displayed/generated field checked must be traceable
to approved guidance and saved observations. Count rewritten records, accepted originals,
rejected fields and unavailable-model cases separately. Model success is not a
comprehension measure. The normal UI can prefer editorial plain-language alternatives;
do not count those as model rewrites or use that UI alone to isolate an AI treatment effect.

## 4. Security-development work programme

The following are selected SSDF practice links, not claims that entire practices are met.
Interpretation and concrete actions are specific to this project.

| SSDF focus | Existing evidence | Required next control |
| --- | --- | --- |
| PO.1/PO.2: requirements and responsibilities | Scope controls; this plan | Author approves matrix and nominates independent reviewer. |
| PO.3/PO.4: tools and checking criteria | Pinned dependencies, Ruff, tests, CI definition | Confirm remote jobs run; make checks required before release/merge. |
| PS.1: protect code | Git history, local-only secrets policy | Verify repository access/branch protections and secret scanning. Do not infer enforcement from a workflow file. |
| PS.2/PS.3: release integrity and records | Wheel verification | Record release commit, wheel SHA-256, dependency inventory/SBOM and private evidence location. |
| PW.1/PW.7/PW.8: design, review and tests | Security boundaries and negative/regression tests | Review threat scenarios, run configured dependency/static security checks, triage findings and retain decisions. Ruff is not a vulnerability scanner. |
| RV.1/RV.2/RV.3: vulnerability response | Dated defect/testing records | Maintain the register below, advisory monitoring and root-cause regression tests. |

Threat scenarios to review: malicious device metadata/XML, prompt injection, unauthorised
scan targets, stolen session tokens, credential leaks, path traversal, interrupted JSON
writes, dependency compromise and misleading reports. Treat device names/adverts as
untrusted claims. Keep Pi-hole secrets outside the repository/OneDrive, and never upload
raw home-network evidence to a public scanner or CI artifact.

Update, 29 September: pinned pip-audit, Bandit and detect-secrets gates are implemented
and locally verified; commands, data-sharing behaviour and reviewed alerts are recorded
in [release checks](release-checks.md). CI configuration does not prove remote enforcement.
Record vulnerabilities as software defects, separate from network-scan review-item
severity. Do not suppress findings merely to make a check green.

## 5. Verification procedure, in execution order

1. Capture Git HEAD plus a source-file SHA-256 manifest because this working tree has
   uncommitted changes. Record Python, OS, Nmap, model and prompt versions. Hash normal
   saved reports before checks. Use isolated `APP_DATA_DIR` for every test job.
2. Confirm current default-route private network equals the authorised home scope;
   check for existing active scans, Nmap, Ollama and writable isolated storage. Stop on
   scope mismatch, missing permission or overlapping active work. Do not widen the scope.
3. Run one Light scan via the authenticated API with retained XML. Copy only relevant
   historical reports into isolated storage for naming comparisons; preserve originals.
   Save progress transitions, elapsed time, coverage, findings, name sources and AI counts.
4. Run `python scripts/check.py --browser` separately: synthetic network/provider data,
   no live probes. Use `--ollama` only when a separate real-model check is required;
   do not compete with the live scan for the model. Record failures before fixes/reruns.
5. Reopen the completed live report at desktop/mobile sizes. Check all finding panels,
   refresh, evidence limits, original guidance and first actions. Verify saved report
   hashes are unchanged by viewing. Do not click actions which start another live scan.
6. Independently replay retained XML through parser/rules; compare facts and findings.
   Audit normal saved reports read-only and compare their pre-test hashes. A successful
   replay checks consistency, not scanner sensitivity or the absence of vulnerabilities.
7. Run `python scripts/check_package.py`: fresh wheel/environment, dependency consistency,
   pages/assets and demo create/read/reopen. Do not install over the user's running app.
8. Review module ownership, import/asset reachability and largest files. Refactor only
   with a demonstrated responsibility boundary and regression coverage. Re-run affected
   checks after any code change; never delete saved evidence as cleanup.
9. Fill the evidence record and [traceability matrix](quality-traceability.md). Assign
   PASS for an observed criterion, FAIL for a violation, PENDING for unexecuted checks,
   or LIMITED for evidence which covers only part of a criterion. Unreachable devices
   are a coverage outcome; honest failure handling can pass while device assessment remains incomplete.

Stop live work on unexpected scope, signs of disruption, persistent storage failure,
or the user's instruction. Preserve acquired evidence and record the stopping reason.
Never rerun a failing live scan indefinitely to obtain a clean report.

## 6. Evidence, configuration and release control

Each record includes execution time/timezone, code identity (HEAD plus manifest),
versions, authorised profile, commands, artifact references, observed values, criterion
status, limitations and next owner. Keep raw addresses/names/XML/screenshots private in
ignored local artifacts. Commit only sanitised aggregate summaries and test fixtures.
Retain evaluation evidence until the dissertation/project retention decision; preview
any cleanup and back up before recovery. No automatic deletion or migration is authorised.

Proposed release gate (not all enforced in CI yet):

- [ ] Author-approved requirements and scope; independent review recorded.
- [ ] Tests, lint/format, browser startup/upgrade/refresh and package checks green.
- [ ] Security/dependency/secret checks reviewed; no unaccepted critical/high software defects.
- [ ] Supported-platform CI results linked; repository protection settings verified.
- [ ] Known limitations and changed behaviour documented; rollback/install instructions tested.
- [ ] Release source and wheel hashes recorded; restore from a copied backup tested.
- [ ] Any claimed real integration and comprehension benefit supported by its own evidence.

Local passing tests permit continued prototype evaluation, not an unqualified production
release. Never equate a workflow definition, a test count or coverage percentage with
independent assurance. Pending claims must remain excluded from the dissertation results.

## 7. Risk/defect and corrective-action register

Owner for all open actions: project author; implementation support by assistant only
when requested. Dates below are milestones, not invented calendar commitments.

| ID | Risk/defect | Priority | Existing mitigation / remaining action | Due / state |
| --- | --- | --- | --- | --- |
| R01 | Cached module blocks dashboard startup | High availability | Reproduced; versioned assets, no-store and recovery regression added; baseline browser regression passed | Local verification passed 28 September; retain regression before release |
| R02 | User interprets incomplete scan as safe | High interpretation risk | Explicit coverage, fixed severity and missing-check messages; complete controlled comprehension study | Before effectiveness claim / open |
| R03 | Scan runs on a shared/unauthorised network | High | Server scope validation and preflight; confirm permission each live session | Every live run / ongoing |
| R04 | Storage contention/crash loses later progress | High | Atomic checkpoints, backups, bounded locks; adversarial tests and copied-backup recovery | Every storage change / ongoing |
| R05 | AI/editorial wording confounds comparison | High research validity | Separate original, actual model output and editorial display; prepare controlled synthetic conditions and reviewer scoring | Before participants / open |
| R06 | Pi-hole or Linux/Deep behaviour assumed from mocks | Medium | Mark unverified; obtain real host/authorisation and ground-truth lab evidence | Before integration/platform claim / open |
| R07 | Vulnerable dependencies/secrets enter a release | High | Lock files and local-secret boundaries; implement/triage scanning and inventory, verify repository protections | Before release / open |
| R08 | Large controllers become hard to change safely | Medium | Existing layering/tests; review supervisor, AI service and scan-page responsibilities before extensions | Next relevant feature / open |
| R09 | Dependency deprecations break future upgrades | Medium | Baseline records Starlette/httpx and pytest-asyncio warnings; test compatible upgrades in isolation without hiding warnings | Before dependency/Python upgrade / open |
| R10 | Unpinned build toolchain weakens reproducibility | Medium | This wheel hash is recorded; pin/review build tooling and retain dependency inventory before release | Before reproducible-build claim / open |
| R11 | Discovered/checked counts or mobile layout confuse beginners | Medium | New baseline identifies ambiguous top count and a low-positioned first action; clarify labels/layout with partial/empty-case regressions and reader testing | Next usability change / open |

For a new defect record: ID, affected requirement/version, reproducible symptom, impact,
containment, root cause, change reference, failing-then-passing test, residual limitations
and reviewer. Critical/high defects block release; investigate before new feature work.
If a deadline cannot be met, the author records a revised date and scope restriction.

### Risk follow-up - 29 September 2026

The register above preserves baseline decisions. R04 now has a passing real-report
copied-backup drill; routine operator backup ownership still needs confirmation. R07 has
passing local security gates, but remote checks/protections and independent review remain
unverified. R09's pytest dependency/deprecation problem is resolved in the isolated updated
test environment; one Starlette/httpx warning remains. R11's layout/count corrections are
implemented and browser-tested; reader comprehension is not yet measured. External
evaluation, independent approval and reproducible-build gaps remain open.

## 8. Completion and remaining actions

The plan is complete as an execution specification. Its adoption and release sign-off
are pending the author; standards conformity is not claimed. The new baseline evidence
is recorded in [the execution record](quality-evidence-20260928.md): 306 Python and
31 JavaScript tests passed; a new 4m15s Light run checked 13 of 14 discovered devices,
and all nine explanation records validated. The remaining device stayed explicitly
unchecked. The record separates passed local checks from pending external evaluation.
Next milestones after that baseline: security/repository gates, controlled Deep/Pi-hole/
Ubuntu checks, then the nontechnical-reader study using the corrected comparison design.
