# Safe workspace, architecture and GitHub audit — 16 October 2026

Follow-up: [WebKit layout changes and diagnosed Windows launch block](webkit-reflow-20261016.md).
That work does not turn the previously failing remote checks into a verified pass.

## Scope and baseline

Reviewed the local source, tests, dependency locks, asset/import reachability,
packaging and the connected GitHub repository. Started with a clean worktree at
commit `8b15f28`; the GitHub `main` branch pointed to the same commit. The complete
remote tree contained 337 files and was not truncated. Source reviewed locally
therefore corresponds to that published baseline; the cleanup below is **local
and uncommitted**, not a new GitHub result.

No network/device scans, live AI generation, device-name refresh, Pi-hole requests,
normal report repair/deletion, Git pushes, remote workflow runs or repository-policy
changes were performed. Dependency advisory requests send package names/versions
only. Private configuration, model prompts and scan evidence were not uploaded.

## Small organisation changes completed

- Shared CPE service eligibility moved into `_service_identity` in `scanner/cpe.py`.
  The public exact-version and product-only helpers retain separate parsers and
  confidence/ambiguity rules. Existing focused regressions passed: 52 cases.
- Browser geometry uses `component_boxes` to sample component/child rectangles in
  one browser task. This addresses timing-sensitive comparisons during Firefox's
  asynchronous scrolling, without sleeps or relaxed geometric bounds.
- Three obsolete text expectations were updated to the existing simpler wording.
  Page-selection bounds, unknown-feature uncertainty, protection advice and the
  warning against interpreting an empty report as proof of safety remain asserted.
- The Windows `ipconfig` unit fixture now explicitly selects the Windows branch on
  Ubuntu too; it no longer tests Linux routing with Windows command output.
- Both local CI job definitions now create an isolated virtual environment before
  installing dependencies. This prevents unrelated preinstalled runner tools from
  invalidating `pip check`. Parsed the workflow and both embedded Python blocks.
  This definition has **not** been pushed or verified on a new GitHub run.

No app files were deleted. All 29 static assets have a template/import reference;
there were no broken static references in the source graph. All 76 Python modules
are reachable when normal parent-package initialisation is included. Three naive
unreachable results were package `__init__.py` markers, not unused implementations.
Dynamic paths/public APIs still need human review; reachability is not proof that
every branch runs. Virtual environments, build outputs, old backup archives and
ignored evidence were retained rather than treated as disposable user data.

## Current architecture assessment

The layered, local single-user architecture remains appropriate; this audit does
not justify a Flask or database migration.

| Layer | Responsibility and boundary |
| --- | --- |
| Browser templates/modules | Display saved facts, reading preferences and explicit user actions; no direct scanner execution. |
| FastAPI/session/scope | Loopback host/origin, session/CSRF and explicit authorised target validation. |
| Supervisor | Five admitted jobs, two scanner workers and one scan-analysis slot; bounded queues, execution and cancellation. |
| Scanner/enrichment | Argument-array Nmap execution, allowlisted scripts and bounded parsing/enrichment; incomplete checks remain incomplete. |
| Rules and explanations | Deterministic findings/severity, then local reviewed-choice AI validation; AI cannot authorise probes or invent CVE IDs. |
| JSON storage | Per-folder instance ownership, locks/revisions, atomic bounded writes, checkpoints, recovery and separate user annotations. |
| Optional references/runtime | Explicit bounded NVD research and app-lifetime Ollama maintenance; neither broadens scan scope. |

Important retained limits: desktop single-user trust model; finite JSON/cache and
recovery budgets; no automatic recovery purge; no distributed-worker/remote-user
guarantees. Model availability does not guarantee accepted output. Pi-hole backend
code is still referenced for compatibility/configuration and is not dead code just
because the UI option was removed.

## Open issues and priority

1. **High verification priority — GitHub is not green.** The inspected
   [published run](https://github.com/YoanKirilov/MSc-Major-Project/actions/runs/38810689390)
   has a successful security job, two failed test jobs and two cancelled test jobs.
   Ubuntu/Python 3.12 reported **17 failed, 1,259 passed, one skipped**. Its failures
   include nine wording assertions, a Windows-fixture-on-Linux assertion, three
   timing-sensitive Firefox geometry comparisons and four WebKit layout cases.
   Windows/Python 3.12 failed `pip check`: preinstalled `pipx` required newer
   `filelock`/`platformdirs` than the application's valid pins. The local isolation/
   test cleanup addresses identified causes, but only a future remote run can
   establish cross-platform results. No checks were removed or made optional.
2. **Medium — CVE client/server timeout mismatch.** `cves.mjs` requests 95 seconds,
   but `api.js` caps every request at 60 seconds. The database budget can take 45
   seconds and reviewed AI context another 40. The client can therefore report an
   unconfirmed lookup while the server is still saving it. Plan: align an explicitly
   bounded CVE deadline and test the actual 95-second request, or separate reference
   retrieval from slower explanation preparation. **Not changed in this audit.**
3. **Medium hardening — intended headers are only metadata.** `base.html` declares
   `frame-ancestors` in a CSP meta tag, which browsers do not support there, and
   declares `X-Content-Type-Options` as metadata instead of an HTTP response header.
   The middleware sets Cache-Control, not those headers. Plan: deliver the existing
   policy and `nosniff` as real response headers and test HTML/static/API/error and
   print/share behaviour. This is an ineffective defence, not proof of an exploit;
   host/origin/session controls remain in place. **Not changed in this audit.** See
   [MDN frame-ancestors](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors)
   and [MDN nosniff](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Content-Type-Options).
4. **Medium UX verification — unresolved WebKit overflow.** GitHub found narrow/
   enlarged-text Settings and related reflow failures in WebKit. Local WebKit exits
   during launch, so Chromium/Firefox success cannot clear those failures. Plan:
   reproduce in a working Linux WebKit environment and inspect native controls and
   grid/min-content sizing; retain the overflow checks. Physical Safari/phone and
   assistive-technology/participant tests remain separate, unperformed evaluation.
5. **Repository governance — no enforced checks.** The public `main` branch metadata
   reports `protected: false`, required checks off and the ruleset list is empty.
   The dedicated protection endpoint returned integration-permission 403; the
   branch/ruleset observations are the evidence, not an assumed administrator audit.
   Recommend required checks and PR review after CI is reliable. Changing repository
   permissions/rules needs an explicit user request and was not attempted.
6. **Maintainability — split large controllers gradually.** `scan.js` is about
   1,278 lines and `jobs/supervisor.py` about 1,080. They retain multiple reading/
   editing and orchestration responsibilities. Plan focused extraction of report
   notes/controller code and stage orchestration behind regression contracts, not
   deletion or a wholesale rewrite based on line count. Runtime currently relies
   on the provider's private generation lock; a public preload/slot interface would
   reduce that coupling. No runtime defect is asserted from module length alone.
7. **Publication/privacy review.** The current remote tree has no obvious tracked
   `.env`, raw scan JSON, secret directory, private key or environment/build folder.
   Secret scanning found no alerts, but 35 documentation files contain home-range
   examples and/or device-label references. Some are intentional examples, others
   dated live evidence. Review/redact household-identifying material before public
   publication; do not silently rewrite research records or Git history. No real
   credential incident is established, and historical secret contents were not
   exhaustively audited.

CI's isolated environment uses GitHub's documented per-job
[GITHUB_PATH mechanism](https://docs.github.com/en/actions/reference/workflows-and-actions/variables).
Further CI improvement: split offline/platform and browser-engine jobs to avoid
making every OS/Python combination repeat the entire three-engine browser matrix.
Do not silently increase timeouts or skip engines to hide failures.

## Verification and limits

- Initial full offline gate: 860 Python passed, five Windows link-privilege skips,
  252 JavaScript passed, 27 syntax checks; lint/format passed.
- Initial local reproduction: **14 passed, six failed** in 20 Chromium/Firefox cases;
  all six failures were the three obsolete wording expectations across both engines.
- Final same selection `safe-audit-browser-20261016-final/`: **20 passed**, no skips,
  156 seconds. The first failed run is preserved in `safe-audit-browser-20261016-a/`.
- Final full offline gate `.test-artifacts/checks-5c52ae0f6e/`: **860 Python passed,
  five environment skips, 252 JavaScript passed, 27 syntax checks**, Ruff and 181-file
  formatting passed. Local Python is 3.14.2/Windows, not an Ubuntu/3.12 result.
- Final security `.test-artifacts/security-7417ab2811/`: no known advisories in either
  pinned dependency graph, **zero secret alerts**, 16 reviewed-category low Bandit
  alerts and zero medium/high. The low alerts cover fixed/trusted-PATH subprocess
  operations, best-effort browser opening and skipped malformed enumeration records;
  they are not erased or broadly suppressed. This is not security certification.
- Both existing runtime and quality environments pass `pip check`.
- Final offline installed package `.test-artifacts/package-2a9eea632b/` passed seven
  pages, 29 assets, dependency checks and synthetic report create/reopen/delete/Undo.
  All **115** app files match the build snapshot, installed wheel and current source.
- Final `git diff --check` passed. GitHub `main` was rechecked at `8b15f28`; no remote
  update has been made, and the local working changes are not represented by that CI.

Not verified here: fresh Ubuntu/3.12 execution, a successful WebKit launch, physical
devices/screen readers, reader comprehension, live scanner accuracy, live Pi-hole,
new local-model inference, exhaustive Git history or a new remote CI run. No green
claim for those areas is inferred from a passing local offline suite.
