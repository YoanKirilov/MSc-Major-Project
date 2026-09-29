# Quality-plan execution record - 28 September 2026

Record ID: QE-20260928-01. Criteria fixed first in `quality-plan.md` version 1.0.
Criteria were written before one authorised Light run and isolated checks.
No formal conformity or independent sign-off is claimed.

## Pre-execution decision

Current detected and saved network matched the previously authorised home /24.
User explicitly requested another live test. Pi-hole is not configured, so no actual
Pi-hole test is included. Deep, router changes, packet capture and participant study
are excluded. Preserve normal reports and use an isolated data folder.

## Reproducible identity and artifact locations

Application source baseline: Git `5c4e933134fe7719e7e407865010f681dea242c7`.
The source was clean at capture; the three new quality documents were untracked.
The 113-file source/configuration SHA-256 manifest also identifies the tested contents.
Manifest: `.test-artifacts/quality-baseline-65hdkpxu/baseline.json`, SHA-256
`d9711b2faffb2a0aee93dd3fc0ed66bbe00e07a830e6311b8a216a436cf0a18a`.
Normal saved-report baseline: 34 JSON reports hashed before the scan.

- Windows 11 build 26200; Python 3.14.2; Node 24.13.0.
- Nmap 7.991; local Ollama model `llama3.2:3b` available at preflight.
- Live artifacts: `.test-artifacts/live-review-8ji2g_ha/`.
- New scan ID: `f8cd47c1-2355-4181-83bc-30dc166d8fc4`.
- Regression artifacts: `.test-artifacts/checks-8bf1732908/`.
- Installed-wheel artifacts: `.test-artifacts/package-969c0887ea/`.
- Wheel SHA-256: `25a9087b2493433f4a582ff9a7b8a0836826f9e3e5ebed9b843ab98f4b96ee42`.

Raw private evidence and machine manifests remain in ignored local artifact folders,
not the public documentation. Times below use UTC; local BST is UTC+1.

## Automated and packaging checks

PASS: `.venv-brief/Scripts/python.exe scripts/check.py --browser`:
306 Python tests passed (including the real Edge workflow with synthetic scanner and
provider responses), one separate live-provider test deselected; 31 JavaScript tests
passed; seven JS syntax checks passed; Ruff lint and format passed (92 Python files).
Real Ollama is exercised by the separate home scan, not counted as that deselected test.

PASS: `.venv-brief/Scripts/python.exe scripts/check_package.py`: built and installed a
wheel in a fresh environment, `pip check` found no broken requirements, all four pages
and eight static assets loaded, and demo read/create/reopen passed. This did not replace
the user's existing runtime or restart its server. The build toolchain is not fully
locked (`setuptools>=68`, `wheel`), so the wheel hash identifies this artifact rather
than promising reproducible byte-for-byte builds.

Warnings: 1,082 regression warnings, principally repeated pytest-asyncio event-loop
policy deprecations and the Starlette/httpx TestClient deprecation. They are not 1,082
distinct defects, but compatible toolchain upgrades need verification before future
Python upgrades. No warning suppression or dependency changes were made.

Execution issue: the sandbox initially denied writing a newly created temporary
artifact directory. Re-running the diagnostic with normal Windows permissions
succeeded before the scan. This was a test-environment permission failure, not a
silently repaired application result. Reading the isolated wheel hash required the
same permissions.

## New live scan and report review

Executed after the plan was written: 18:56:32-19:00:47 UTC (19:56:32-20:00:47 BST),
**4 minutes 15 seconds**, including enrichment and Ollama. Authenticated API submission
and progress polling used the actual `.venv` runtime and isolated storage. No overlapping
saved active job was present. This is a new run, not the earlier afternoon result.

| Measure | New observed result |
| --- | --- |
| Discovery / service checks | 14 discovered; 13 completed; one unreachable after two attempts |
| Saved outcome | `partial`, phase `finished`; missing coverage preserved |
| Open services | 13 |
| Review items | 8: four low priority, four informational; no medium/high findings in selected checks |
| Device names | 3 current names: two mDNS, one reverse DNS; no historical name fallback; no name conflicts |
| mDNS | 4 advertisements from 2 hosts |
| Pi-hole | Disabled/unconfigured; none of these names came from Pi-hole |
| AI | 9 ready records (overview + 8 items), two requests, changed fields in every record; zero rejected fields/fallback records |
| Versions | App 0.1.0, rules 1.2.1, profiling 1.1.1, prompt 4.2.1, wording schema 1.0.1 |
| Saved JSON size | 194,345 bytes, below the 20 MiB boundary |

Observed polling stages: queued, discovery, service scan, enrichment, analysis,
finished. Analysis progressed from 0/9 with six active records, to 6/9 with three
active, to 9/9 finished. Network collection remained distinct from AI preparation.
Completed records may retain individual original fields; nine records with changed
fields does not mean every sentence was rewritten.

PASS factual consistency: retained XML for all 13 completed hosts reproduced every
saved service fact; deterministic replay reproduced all eight findings, excluding
generated timestamps. The remaining host's retained XML independently reproduced
`HostUnreachable`; its two failed attempts remain recorded. The underlying reason
(sleep, disconnection, filtering, etc.) cannot be established from that observation.
Replay is not an independent ground-truth accuracy study or proof of network safety.

PASS source-bound wording: all nine records matched the approved, fact-bound choices,
with original guidance retained. Real Ollama was used. This validates the output
contract, not human comprehension, and the interface also uses editorial alternatives.

PASS actual-report browser checks: Edge, desktop 1440x1000 and mobile 390x844; all
eight finding panels, 13 technical device rows and 14 coverage cards (including the
unchecked device), report refresh, zero page errors/failed HTTP responses and no
horizontal page overflow. Viewing did not change the saved report hash. Screenshots
were visually inspected; selected display text and panels are retained in `review.json`.
Synthetic browser regressions separately cover startup recovery, in-progress refresh,
AI failure/retry and Light/Deep Run again without unwanted scanning. No second live
scan was triggered by browser verification.

PASS normal-data preservation: all 34 normal saved reports validated read-only and
their pre/post hashes match (21 completed, 8 partial, 3 failed, 2 cancelled). The
113-file source manifest also remained unchanged. See `comparison.json` in the baseline
folder and `evidence-audit.json` / `quality-metrics.json` in the live folder.

### Beginner-reader review: LIMITED, not a participant study

The headline says "Scan finished; 1 device could not be checked." The lead explains
what a service means; review items are explicitly not proof of a break-in. Device cards
keep unknown identity and incomplete coverage visible. Finding panels distinguish
observations, meaning, missing checks and first actions; web-page instructions warn
against entering credentials over HTTP or bypassing certificate warnings.

Concrete next changes to evaluate, recorded before implementation:

1. Clarify the top statistic: "Devices observed: 13" currently means saved device
   results, whereas discovery found 14. Prefer "Devices checked: 13 of 14" with the
   separate unfinished count. Acceptance: counts match coverage in complete, partial,
   empty and advertisement-only fixtures; no implied completed check.
2. Move a short first-action block above the large statistics panel on mobile. The
   current top screen explains the limitation but requires scrolling to the recommended
   action. Acceptance: at 390x844 the priority action is discoverable without opening
   technical details; retain the coverage warning and safe-device-identification advice.
3. Put raw protocol/port labels behind optional details in beginner device cards and
   explain "confidence in assessment" in ordinary language. For inferred names such
   as `http-proxy` / `https-alt`, never imply the service was positively identified.
   Acceptance: keep factual labels and qualifiers in technical view; test both views.
4. Reduce repeated HTTPS-check instructions while preserving the credential warning
   and starting-page-only limitation. Assess actual comprehension using the controlled
   study, not merely shorter text or an assistant's impression.

These are improvement opportunities, not findings of a new critical software fault.
Nontechnical-reader effectiveness remains unmeasured.

## Code organisation review

PASS within the inspected scope: import reachability, shipped-asset traversal,
lint/format and regressions. No demonstrably unused shipped module or asset was found;
reachability does not prove that every function/branch is used. No source file or saved
report was deleted. Existing collection, rules, storage, explanation and UI boundaries
remain suitable for this local single-user prototype. Keep FastAPI and JSON.

Future bounded refactors (not required to pass this baseline):

1. `app/jobs/supervisor.py` (893 lines): `_run` owns discovery and a large nested
   per-host retry/checkpoint pipeline. Before extending profiles, extract a host-check
   operation with explicit results while preserving cancellation, semaphore limits and
   checkpoint ownership. Existing supervisor/process regressions must stay green.
2. `app/static/js/scan.js` (720 lines): split device-card/table rendering from page
   orchestration when changing report UI; keep pure formatting in existing shared
   modules and preserve cache-versioning/import/browser tests.
3. `app/explanations/service.py` (556 lines): provider transport and batching/persistence
   can be separated before another provider is added. Do not duplicate the already
   extracted validation, retry and approved-wording logic.

Line counts include blank lines and are observations, not automatic failure thresholds.
No behavioural refactor was justified during this evidence-only baseline. Documentation
was organised around the plan, matrix and execution record. The reader-study kit now
explicitly separates model output from editorial UI text to avoid a confounded comparison.

## Release decision

LIMITED: the measured local prototype checks passed; no new blocking regression was
found in their scope. The network report is still incomplete for one device, and no
security/production-readiness claim is warranted. Independent review, remote CI/Ubuntu,
actual Pi-hole, controlled Deep ground truth, dependency/secret security controls,
controlled reader-study views and participant evaluation remain pending. Recovery has
synthetic tests; an operational restore drill from a copied real backup remains pending.

Next owner: project author. Priority order: approve this plan/assign reviewer; implement
and triage security/repository gates; clarify device counts and mobile first actions;
pin/test build-tool upgrades; then authorise the separate integration/lab evaluations
and reader study. Keep each change tied to the Q IDs and rerun its regressions.
