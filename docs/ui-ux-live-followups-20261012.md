# UI/UX repeat check and execution plan — 12 October 2026

Status: six numbered follow-ups implemented (five application/UI changes and one
test-harness fix). New live scans, actual-report checks, the final full regression
gate and offline installed-package verification passed. Open limits remain below.
This follows [the earlier readability fixes](readability-fixes-20261012.md), not a
replacement for historical scan evidence. Preserve every finding, port, individual
action status and original report. No Pi-hole or external CVE lookup is in scope.

## Evidence and execution order

Baseline: offline gate passed 597 Python and 107 JavaScript tests in
`.test-artifacts/checks-f4e44efa40/`. The isolated running viewer reopened copied
12 October Light and Deep evidence without scan/edit submissions. New authorised
Light `192.168.0.0/24` and Deep this-PC `192.168.0.216` jobs were running in
`.test-artifacts/ui-followups-live-20261012-5d392f/` when the plan was written.
Their completed results are recorded below. Do not resubmit them on refresh.

1. **Fix narrow technical-table disclosure controls.** The expanded Deep table's
   name/additional-detail summaries measured about 21 CSS pixels wide at
   320/390/768-pixel viewports and wrapped into tall, nearly single-letter columns.
   Whole-page overflow tests did not detect this. Give table columns readable
   minimum widths and retain scrolling within its labelled, keyboard-focusable
   container. Test the expanded table and its actual controls, including rich data.
   A small width alone does not establish a WCAG failure: spacing exceptions require
   separate assessment. It is a confirmed readability/target-usability defect.
2. **Fix checklist availability wording and empty-filter controls.** Collapsed
   checklists say “Showing 28 of 28 review tasks” although the controls are closed;
   a no-match Checked filter leaves both bulk disclosure buttons enabled. Describe
   tasks as available, explain how to open them, and disable expand/collapse when
   no checklist matches. Preserve focused/in-flight edits and every action.
3. **Expose per-checklist saved status before expansion.** Every summary currently
   says only “Record your review (2 tasks).” Show concise counts for Checked, Need
   help and To check from the existing saved notes. Under filtering distinguish
   available rows from the full action count. Missing notes must say status
   unavailable, not invent unchecked status. Do not rebuild controls or move focus.
4. **Add an explicit device filter to review items.** A new labelled native select
   lets beginners read one device at a time without knowing its address or typing a
   technical term. Show per-device counts, retain All devices, explain that this
   filter does not hide device cards or checklist tasks, and preserve it on refresh
   as bounded tab/report reading state only. Related-item links must still open
   their target even when it was outside the current filter. No scan/API mutation.
5. **Explain repeated unidentified connection replies together.** If one device has
   multiple R07 informational tcpwrapped observations, provide a short contextual
   note: these are separate connection replies, not confirmed software problems;
   their purpose and cause were not identified. Keep every individual item and
   independent action reachable; do not guess software from port numbers.
6. **New verification finding: reserve browser-safe test ports.** The broad gate
   passed 720 tests but one fixture failed before loading its report because the
   OS chose port 5061, which Chromium blocks (`ERR_UNSAFE_PORT`). Record this as a
   test setup error, not a scanner or UI failure. Replace unbounded port-zero
   reservations in browser fixtures with one shared, bounded loopback helper using
   the high ephemeral range and retaining the socket through server startup. Do
   not change app port 8765, open an external interface or disable browser safety.

## Basis and verification

Use ordinary words and nearby explanations for unfamiliar terms, following
[W3C cognitive-accessibility guidance](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o3p01-clear-words/).
Size and space controls according to
[WCAG 2.2 target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html),
while keeping task titles and statuses visibly associated, as illustrated by the
[GOV.UK task-list pattern](https://design-system.service.gov.uk/components/task-list/).
These are design references, not a certification claim.

After recording new live facts, apply the items in order and add focused pure-JS
and Chromium/Firefox/WebKit regressions for filtering, status projection, reload,
focus, technical-table targets and no extra requests. Replay saved XML/rules and
revalidate AI text against selected facts. Reopen the same new evidence after
presentation-only changes rather than starting unnecessary scans. Verify hashes
and stop only owned helpers; leave the normal app untouched.

## Open limits

The intermittent Windows asyncio socket-close diagnostic remains investigated,
not fixed or suppressed. Absence in one run is not proof of a runtime fix.
Real-reader comprehension, assistive-technology/physical-phone evaluation and
Ubuntu/lab ground truth are still required. Display-only grouping must not merge
findings or mark several independent actions Checked together. No source deletion
is justified merely by a file being absent from one scan path.

## Implementation and actual results

All five planned application changes are implemented. `finding-list.mjs` provides
pure device/count and repeated-reply context helpers; `scan.js` only applies reading
filters, keeping every original finding. `report-view.mjs` bounds/restores the
device choice and resets nonexistent choices to All devices. Related-item links
clear the device restriction. `notes.mjs` projects saved checklist status in place;
disclosure controls affect available checklists only, not task statuses. CSS gives
technical columns readable minimum widths and disclosure targets a 44-pixel height.

| New live result | Light | Deep this PC |
| --- | --- | --- |
| Checks completed | 6 of 6 discovered devices | 1 of 1 selected device |
| Answering features | 10 | 14 |
| Review items | 7: three Low, four informational | 4 informational |
| Scan errors / unfinished checks | 0 / 0 | 0 / 0 |
| Duration through Ollama | 249.6 seconds | 534.2 seconds |
| AI records revalidated | 8 | 5 |

Light ID: `c4fc2135-6a0b-46a0-86bb-98ff0219bd4d`.
Deep ID: `fbe579c3-6824-4a3c-8540-07cc16a383cd`.
These reports are in the isolated test folder, not silently added to normal history.
Raw XML replay matched **111 service records and all 11 findings**. All **13**
accepted AI records revalidated with no rejected fields or fallbacks; selected AI
input contained no addresses, names, MACs, network range or raw XML. Refresh and
automatic report opening after analysis passed with exactly two scan submissions.
Deep retains the expected local-self-routing limitation, not an error or an
internet-exposure finding. This run identified four feature names through probes,
unlike the earlier tcpwrapped snapshot; changing responses are not proof of a fix
or compromise. Other unknown/port-inferred features remain qualified and visible.

The finished read-only viewer passed **16 engine/profile/viewport combinations**
in `browser-check-07e5aa8f/`: Chromium 320/390/768/1440 and Firefox/WebKit 390/1440.
It checked expanded technical-table targets, device-filter reload, empty checklist
filters, unchanged per-action status, reading alignment, grouped feature evidence,
selection, exact-address search, history and Run again. No page errors, horizontal
page overflow or extra scan/edit submissions occurred. Visible technical-table
summary targets were at least 44 by 44 CSS pixels. All **16 served CSS/JS assets**
matched source bytes with `no-store`; original, copied and reopened evidence hashes
were unchanged. Owned scan/viewer helpers were stopped and normal PID 35732 on 8765
was left running; no listener remained on 8766.

All 11 actual review-item explanations were captured and editorially reviewed from
a beginner perspective. They retain HTTP/HTTPS page limits, conditional purpose
and practical directions for streaming/name lookup/Windows/VMware, permission
and password precautions, and the distinction between a reply and a vulnerability.
Screenshots were visually spot-checked. This is not participant comprehension data.

Intermediate verification failures are retained, not counted as passes: the first
focused run assumed desktop tables must overflow (6 passed/3 test failures), and
one gate stopped on test-line formatting. The first two live-viewer attempts tested
hidden nested controls as zero-sized, then confused a column-width bound with a
nested target's intended 44-pixel bound. The corrected viewer passed; none of those
failures indicated missing scan evidence. Nine focused cross-browser regressions
passed in `.test-artifacts/ui-followups-focused-20261012-941e12/`; the final full
gate is tracked separately below.

The current architecture document had one stale prompt-version reference (4.2.2)
despite its newer introduction. It now consistently records 4.3.0; dated evidence
was not rewritten. All 67 application modules are reachable from entry points when
implicit package imports are included, and all 15 shipped JS modules have references.
No unused source-file deletion was justified. This checks reachability, not every
possible dead branch or production-readiness property.

## Broad-gate finding and verification follow-through

The first broad three-engine run, `.test-artifacts/checks-19e55d8f95/`, had **720
passes, one setup error and one real-provider test deselected**. A browser fixture
received OS-assigned port 5061; Chromium rejected it before the report loaded.
[Chromium's port restrictions](https://raw.githubusercontent.com/chromium/chromium/main/net/base/port_util.cc)
confirm that this is a blocked port. No application result was bypassed or marked
successful to hide the error.

The new shared `tests/fixtures/browser.py` reserves a high ephemeral loopback
listener (49152–65535), retains it through Uvicorn startup and bounds allocation
attempts to 64. It closes failed sockets, retries only occupied/OS-reserved ports,
and propagates other errors. Seven browser test modules now use it, including both
workflow listeners. There are no browser safety overrides or application-port changes.
Five listener unit cases passed, covering actual reservation, two collision causes,
exhaustion and unrelated errors. Custom enterprise restrictions remain an external
test-environment limit.

After the port fix, 21 focused cases passed across all three engines in
`.test-artifacts/ui-safe-port-focus-20261012-221aed/`, including the previously
affected geometry case family and all new review tasks. No app source changed
after the successful actual-report viewer; these later fixes are test-only.

The finished application source passed the separate offline gate in
`.test-artifacts/checks-78fc17432a/` (**597 Python/110 JavaScript**), after the
minimal-DOM report test was taught its new imported helpers. An earlier offline
attempt had failed on that missing test-harness injection; it was not an application
import failure. The later listener changes add five Python cases and two formatted
Python files; their full-gate result follows below.

The repeated loopback diagnostic on Python 3.14.2 passed 11 orderly and 10 abrupt
disconnects, 20 concurrent synthetic subprocesses and post-disconnect responsiveness,
with no captured callbacks. Actual scan/viewer logs likewise had no ERROR,
ConnectionResetError or traceback entries. The known upstream shutdown path is
still not repaired, and these runs do not establish that it can never recur.

Offline installed-wheel verification passed in
`.test-artifacts/package-df236cc3d9/`, using only the existing local wheel cache
and fresh builder/runtime environments. Pinned build/runtime dependency checks,
six rendered page routes, 16 static assets and synthetic demo create/reopen passed.
The normal environment/data were not installed over or used as package test data.
The wheel's complete 91-file application payload also matched the current source
file set and bytes exactly, with no extra stale modules or missing assets.

### Finished-source full gate

`.test-artifacts/checks-edff312679/` passed **726 Python/browser tests and 110
JavaScript tests**, with one optional real-provider test deselected. Ruff lint,
format checks for 146 Python files and syntax checks for all 15 JS modules passed.
The earlier 720-pass/one-setup-error run remains recorded above; it was not relabelled
as a success. The actual local Ollama verification is the new live pair and its
13 revalidated records, separate from synthetic/offline browser tests.

No application-code changes followed the successful live-report viewer or package
verification. Existing evidence, risk priorities, scan scope and data-folder locking
were preserved; no unused app source deletion was justified. Refresh a report to
see the new presentation. The scans were deliberately saved in the test folder,
not copied into normal history or used to overwrite earlier reports.

Next evaluation work is the already-open real-reader/assistive-technology/physical-
phone study and authorised Ubuntu/lab comparison. Keep the intermittent Windows
runtime-close issue explicitly open until a supported fix is verified; the clean
logs here are not such a fix. Pi-hole and real CVE-provider evaluation remain deferred.
