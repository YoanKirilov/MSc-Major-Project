# Report experience execution plan — 6 October 2026

1. Add a visible phase tracker to both scan pages. Deep's single-host check uses an
   activity indicator rather than a completed-device percentage of zero. Show only
   phases the backend reports; show actual completed explanation counts during AI.
2. Add an identification shortcut from the overview to the first relevant device.
   Put nickname controls in a visible device toolbar, retaining detected names,
   source/conflict information and existing cross-report nickname identity rules.
3. Persist a per-finding/action checklist in report annotations: To check, Checked,
   Need help. Require session/CSRF, a finished report, a valid saved action and the
   current annotation revision. Write under the scan lock; never alter findings,
   severity, raw evidence or AI. Reload and reject stale edits without losing other
   notes. Show checklist controls in action details and grouped next steps.
4. Promote the existing conservative comparison evidence into a visible section
   near the overview with a short count summary and expandable per-device details.
   Keep unavailable/incompatible comparisons explicit; do not claim absent devices
   are gone or a matching address verifies identity. Preserve the existing evidence.
5. Add focused storage/API and browser checks for persistence, stale edits, action
   validation, nickname access, search and responsive stages. Run the isolated full
   suite with three browser engines; update evidence and status documentation.

Normal history and unrelated edits are preserved. Local JSON remains the store.
No live network scan is required for these UI/annotation changes. The previous
Windows runtime reset remains a separate open dependency issue.

## Results

All five steps completed.

- Dashboard stages reflect saved backend phases. Deep service checks show Running;
  AI preparation retains exact saved explanation counts. No Nmap sub-stages or
  time estimates are invented.
- The overview opens and focuses the relevant device's naming button. Device
  details and their always-visible naming toolbar share one desktop grid item;
  mobile details stay collapsed until opened. Existing name provenance is retained.
- Checklists persist separately from evidence, survive reopening, synchronise their
  two report controls and preserve keyboard focus. Save/conflict feedback is shown
  beside the edited control. Another tab's stale edit is rejected, not replayed.
- The promoted comparison section reports available versus unreliable comparisons
  and retains the original saved observations and their identity/coverage cautions.

Final command:

```powershell
.venv-quality/Scripts/python.exe -B scripts/check.py --browser --browser-engines chromium,firefox,webkit
```

Passed: **448 Python tests**, **57 JavaScript tests**, Chromium/Firefox/WebKit,
Ruff lint/format and all nine JavaScript module syntax checks. One opt-in real
Ollama test was deselected. Artifacts: `.test-artifacts/checks-e4afab43d9/`.
Responsive coverage includes eight viewport sizes, 100%/200% text and the new
Running indicator. Storage/API tests cover persistence, concurrent stale revisions,
session/CSRF, invalid actions, unfinished reports and unchanged scan-file bytes.
Browser checks cover two-tab conflicts, reopening, paired control updates, focus,
mobile identification and desktop device/toolbar association.

An early security assertion expected 401 where existing CSRF protection correctly
returns 403; corrected the assertion. Intermediate browser runs used old selectors
while device grouping was changed; updated them and reran the full suite successfully.
These failures were not excluded from the final run.

No live Nmap/Ollama/CVE/Pi-hole requests or normal-history changes were made in this
pass. Browser scanner/provider responses are synthetic. Actual reader comprehension,
real-phone accessibility and Ubuntu behaviour remain separate evaluation tasks.
The intermittent Windows socket reset is still open; this work does not repair it.

When no jobs are running, restart **NetGuard: Start backend** and reopen its local
session URL to load the new annotation API and page modules. Do not restart during
an active scan.
