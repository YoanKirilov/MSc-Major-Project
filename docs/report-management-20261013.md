# Bounded report pages and recoverable deletion - 13 October 2026

This change supersedes the unbounded one-entry history feed and the repeated
**Show next report** buttons. It preserves the requested empty initial page and
one-by-one appearance while adding a maximum of 24 reports per page, numbered
navigation, shown-report selection, individual/bulk deletion and Undo.

The number 24 is a product choice requested by the user, not an accessibility
standard. Synthetic checks and an assistant review do not establish WCAG
conformance, physical-device usability or participant comprehension.

## Design references and limits

Numbered page controls and current-page labels follow the approach described by
the [GOV.UK pagination guidance](https://design-system.service.gov.uk/components/pagination/).
That guidance warns against infinite scroll because of keyboard-navigation
problems. This implementation bounds the list to an explicit page and never
automatically advances to another page; the requested within-page one-by-one
scroll reveal remains a custom interaction requiring reader/assistive-technology
evaluation. No cited guidance mandates 24 rows or initially hiding every row.

Named confirmation and recoverable Undo apply the error-prevention principles
for changes/deletion of user-controlled data described in
[W3C SC 3.3.4](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html).
Reduced-motion behaviour follows the user-control principle described in
[W3C SC 2.3.3](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html),
a Level AAA criterion. These references explain the design rationale, not a
WCAG certification or a claim that the entire application meets either level.

## Browsing and selection

Opening Saved reports, clearing filters or submitting a search starts with no
report rows and no report-list request. The first deliberate downward scroll
requests one bounded page with `limit=24`; only its first report appears. Further
intentional gestures reveal cached reports one at a time, never more than 24 on
the current page. A response, layout change or scroll momentum must not reveal
the whole page automatically. Page selection explicitly loads that page and
reveals its first report; its remaining reports follow the same scroll behaviour.

Numbered page controls replace next-report buttons and are repeated after the
list. Whole-library search and filters are applied before server pagination.
After removal, the current page is refreshed; if the last page disappears, the
feed corrects to an available page rather than leaving a dead page selected.
Loading, no matches, unreadable files and retry states remain distinct. A failed
page request preserves the reports already shown until an explicit retry succeeds.

Selection is limited to deletable reports currently shown on the current page.
It does not silently include cached-but-unrevealed rows, another page or every
search match. The top selection control and count support **Delete selected**;
each eligible report also has its own Delete action. Changing pages or filters
does not carry a hidden cross-page selection. Running or unreadable reports do
not offer deletion. Newly revealed rows are not an implicit expansion of a
previous destructive selection.

Deletion opens one confirmation dialog naming the selected reports and explaining
that a private recovery copy remains. **Keep reports** is the safe default;
Cancel/Escape performs no write. Confirmation performs one explicit batch request,
not a scan cancellation. A mixed batch reports each outcome and retains reports
that changed, are busy or could not be removed safely. Destructive requests are
never automatically repeated after an outage or uncertain response.

Entry transitions should be short and layout-stable, without forced focus or
automatic scrolling. Reduced-motion preferences disable the transition. Keyboard
scrolling, native controls, visible focus, labelled checkboxes and truthful status
messages remain required; there is no separate **Show next report** button.

## API and storage contracts

`GET /api/reports` retains authenticated whole-library filtering and pagination.
The history client requests at most 24 reports. Each readable item now includes
the scan `revision`, `expected_notes_revision`, `phase` and `deletable` flag.
Unreadable notes have no usable deletion token; the frontend must not invent one.
The API rechecks eligibility, so an earlier `deletable` flag is not authority to
remove a now-active or changed report.

Removal uses this authenticated, CSRF-protected request:

```json
{
  "reports": [
    {
      "scan_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
      "expected_revision": 2,
      "expected_notes_revision": 1
    }
  ]
}
```

`POST /api/reports/delete` accepts 1-24 unique, canonical report UUIDs and positive
integer revision tokens. Its response contains `results`, `deleted_count` and
`recoverable: true`. Per-item statuses are `deleted`, `missing`, `changed`,
`active` or `unavailable`; successful removal includes a canonical `trash_id`.
One failed item does not turn the other receipts into an all-or-nothing claim.

`POST /api/reports/restore` accepts `{"trash_ids": ["<canonical recovery UUID>"]}`,
again 1-24 unique entries. Its response contains `results` and `restored_count`.
Per-item statuses are `restored`, `missing`, `changed` or `unavailable`. Restore
validates the receipt, original report ID, saved scan/notes revisions and finished
state. It never overwrites an existing report with that ID.

`DELETE /api/live-scans/{scan_id}` remains **scan cancellation**, not saved-report
deletion. Report-management requests do not invoke Nmap, Ollama, CVE lookup or
name discovery, and do not remove shared nicknames/settings or fictional demo runs.

The supervisor holds its admission lock for removal/restoration, rejecting active
scan and standalone AI-retry jobs. The storage operation then takes the shared
per-scan file lock used by evidence/notes writers. Source, state, both revisions
and safe paths are checked inside that protection. Optional notes are not silently
recovered/reset as a deletion side effect. Queued, running, unfinished or actively
analysing documents cannot be removed even if their runtime task is unavailable.

Operations have a cooperative 40-second batch budget and five-second per-item
budget; lock waits are no more than two seconds or the remaining budget. Worker
threads are shielded and drained on cancellation, so admission cannot be released
while an outstanding worker can still move a report. These budgets do not make
an individual blocking operating-system call preemptible.

The exact UUID report directory is moved, not recursively erased:

```text
<data-dir>/scans/<scan-id>/
    -> <data-dir>/.trash/<trash-id>/
```

The report, raw XML, archived guidance, notes and previous copies move together.
A validated `.removal-receipt.json` is prepared under the report lock before a
same-volume atomic directory rename. It records original ID/revisions, recovery
UUID and removal time, without replacing factual scan or annotation files. If
the move fails, factual files remain in place; the preparatory receipt may remain.
The directory move is authoritative, so a later cache-cleanup failure must not
be reported as an unsuccessful deletion. Terminal sidecar status survives Undo.

Canonical UUID validation, resolved-root containment checks and rejection of
symlinks/junctions cover managed parents, locks, folders, receipt files and nested
evidence. The archive walk and total bytes are bounded. No arbitrary filesystem
path is accepted from the browser.

The junction guard feature-detects `Path.is_junction`; when that method is absent,
it checks the Windows mount-point reparse tag. The compatibility branch has
synthetic regression coverage on this Windows/Python 3.14 host. That does not
replace an actual supported-Python-3.11 or Ubuntu execution matrix.

## Recovery and retention limits

Deleting a report hides it from saved-report search/history and recent-device
choices; it is **not secure erasure and does not immediately free disk space**.
Private network addresses, names, raw observations and report notes still exist
in the recovery copy and must not be published.

The recovery folder is bounded to 1,000 entries and 2 GiB, with a bounded tree
inspection and no automatic purge. When full, oversized, unsafe or unreadable,
new removal fails closed and the selected report remains available. Operator
maintenance/retention review is required; automatic expiry and a permanent-delete
interface are not implemented.

**Undo last deletion** restores the last acknowledged batch while its receipt is
available in the open history page. Refresh/navigation or another deletion can
lose/replace that immediate UI action; the recovery folder itself remains. An
operator with the saved recovery UUID can use the authenticated restore endpoint.
For manual recovery, stop the app, inspect the validated receipt and preserve both
copies; never replace an existing `scans/<scan-id>` folder. A dedicated recovery
browser and automatic receipt discovery are not part of this change.

Existing storage-size measurement and offline export allowlists cover active
reports/settings/nicknames, **not `.trash`**. The reported saved-data size is not
total disk usage including recovery copies, and existing offline exports do not
back up deleted-report archives. Preserve those archives separately when needed.

## Loading the updated app

Allow active scans and their explanation phase to finish, then restart the backend
task and reload the browser. Both the new report-management routes and the updated
page/modules must be loaded; reloading only an older backend's browser page cannot
add the new API. Do not interrupt an active job solely to reload the interface.
The running normal app was not restarted by this development/verification work.
There is no scan-document migration, automatic report deletion or provider request.

## Verification record

Backend-focused final command used isolated synthetic JSON under
`.test-artifacts/report-trash-20261013-e`:

```powershell
.venv-quality\Scripts\python.exe -m pytest tests/unit/test_report_trash.py tests/unit/test_library.py -q -o addopts='' --basetemp .test-artifacts/report-trash-20261013-e
```

- 54 passed, five skipped in 3.39 seconds; the skipped actual symlink-creation
  cases require Windows privilege unavailable on this host (`WinError 1314`).
  Five simulated junction-path guard cases passed; they are not represented as
  actual link creation tests.
- Passing cases include active AI/batch partial outcomes, stale evidence/notes,
  request bounds, missing/corrupt evidence, rename failure, expired deadlines,
  archive bounds, admission held during cancellation, cache-cleanup failure,
  terminal sidecar recovery, changed archives, no overwrite and session/CSRF.
- Ruff passed the backend route, management schema, storage helper and focused
  test file. The separate bounded-feed Node suite passed 27 cases before the
  final combined gate; record any later gate independently.
- The compatibility-focused run in
  `.test-artifacts/report-trash-compat-20261013-a` passed 38 cases with the same
  five actual Windows link-privilege skips. The library projection/token run in
  `.test-artifacts/library-projection-20261013-c451d8` passed 31 cases. These verify
  the fallback branch on this Windows 3.14 host, not actual Python 3.11/Ubuntu.

### Final offline gate

`.venv-quality\Scripts\python.exe -B scripts/check.py` completed under
`.test-artifacts/checks-c6afb17f69`:

- 653 Python tests passed; five real Windows link-creation cases were skipped;
  91 browser/live-provider/lab/study cases were deselected by the offline gate.
- All 190 JavaScript tests passed, including bounded page/reveal and report-management
  state contracts. Ruff and 154-file formatting checks passed; 18 shipped JavaScript
  syntax checks passed.

### Installed package

The final isolated offline package check in `.test-artifacts/package-61ac7b9531`
passed six pages, nineteen reachable static assets, synthetic report creation/
reopening/deletion/Undo and demo reopening. Builder and installed-runtime dependency
checks were clean. The independent final source/installed comparison also passed:
96 source application files, 96 installed files and zero hash mismatches.

### Browser runs and remaining verification

An initial smoke passed three cases. The earlier complete Chromium/Firefox run
passed 49 and failed one held-scroll-key test because the harness interacted before
the browser's first-paint baseline had settled. The harness was corrected to wait
two animation frames without scripted scrolling or report loading; no application
contract was weakened to satisfy it. The next run passed all 50 test bodies but
reported two Firefox fixture-lifecycle teardown errors; it was not an all-green
run. Cleanup was corrected to close each fresh fixture-owned browser inside the
active Playwright lifetime rather than encountering Firefox's context-removal
session-store race. No exceptions were suppressed. Three affected Firefox retests
passed before the final complete rerun.

The clean final Chromium/Firefox matrix passed all 50 cases with exit code zero,
no assertion or cleanup failures. Its result is recorded in
`.test-artifacts/history-management-browser-20261013c/results.xml`. These are
scoped synthetic history-management checks, not a complete three-engine browser
gate or a real network scan.

The six affected colour/settings/library/synthetic-workflow regressions also
passed with exit code zero in 97.48 seconds, recorded at
`.test-artifacts/report-management-regressions-20261013-a/results.xml`:

- Profile colours: Chromium and Firefox, two cases.
- Settings/shared shell: Chromium and Firefox, two cases.
- Report-library workflow: Chromium, one case.
- Complete mocked scan/AI/retry/history workflow: Chromium, one case.

The selected regressions are
`browser_test_appearance.py::test_report_name_colour_keeps_scan_type_and_swaps_on_hover`,
`browser_test_settings_ui.py::test_settings_history_errors_scope_focus_and_shared_shell`,
`browser_test_library.py::test_search_picker_titles_nickname_sync_and_identification`
and `browser_test_workflow.py::test_scan_ai_wait_failure_retry_history_and_known_host_rescan`.

Final Ruff and 154-file formatting rechecks passed after the browser-fixture cleanup.
Application files were unchanged between the final installed-file comparison and
these fixture/test-only follow-ups.

Windows previously blocked WebKit startup; that remains a verification limitation
unless a new run proves otherwise. No current WebKit pass or three-engine gate is
inferred from older UI records. Physical-device, assistive-technology and participant
checks remain open, and no live network/provider result is inferred from mocks.

No live scan, provider call or existing-report deletion was performed for this
change. Browser fixtures intercept report-management writes; backend tests operate
only on isolated synthetic folders. Participant, physical-device and assistive-
technology evaluation remains outstanding.
