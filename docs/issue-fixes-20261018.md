# Targeted issue fixes - 18 October 2026

Scope: F1-F3 from [the follow-up audit](follow-up-audit-20261018.md), not its nine
broader recommendations. Local JSON storage and the current page layout remain.
No new scans, name probes, AI generations or public NVD calls are required.

## F1: specific CVE lookup receipts

The browser sends a random UUID `operation_id` with an explicit CVE request. The
backend validates the optional ID and saves it with that service's CVE annotation
after processing. A cache hit also records the receipt but preserves the original
reference date and CVE text; it does not start another NVD request merely to obtain
a newer timestamp. The ID is correlation metadata, not authentication or a device
identifier, and is not sent to NVD or the model.

After a lost reply, GET-only saved-reference recovery requires the matching receipt
before allowing another lookup. An old record, another operation's ID or a newer
revision from an unrelated edit cannot confirm the request. References remain
readable and no POST is automatically repeated. A direct successful POST still
confirms its result, including cached reuse. If no receipt can be obtained, the
client remains honestly unconfirmed and offers reading/reloading rather than guessing.
The pending client state is not durable across navigation; reopening reads the last
saved record and never automatically repeats the previous lookup. The backend's
global lookup lock remains in place.

The metadata is additive: old saved annotations omit it and load with `None`.
Legacy `{}` requests still work; an empty body works with the existing required
JSON Content-Type. Unknown fields/invalid UUIDs are rejected. No historical scan
document, finding, priority or schema migration is rewritten. Receipt-only changes
do not rebuild visible CVE descriptions or collapse open details.

## F2: name-lookup completion independent of evidence changes

The controller now explicitly finishes its waiting feedback using the accepted
latest name record. Identical data and timestamps no longer leave "Looking for a
name" visible. A rejected stale response cannot replace newer notes; missing or
failed results give a final, qualified outcome rather than success or indefinite
waiting. A shared display helper keeps static and completion messages consistent.
Unchanged disclosures retain their nodes/open state; original device names and
scan evidence remain unchanged. No automatic repeat name request is added.

## F3: current evaluation/traceability status

[The verification index](verification-status.md) separates the published commit,
uncommitted source, hosted baseline, local synthetic tests, real scans, saved-only
reopening, model readiness/generation and unperformed participant evaluation.
`evaluation.md` now describes the current browser workflow and API-only explanation
recovery accurately. `quality-traceability.md`, README and testing notes point to
the current index while retaining dated historical records.

## Verification

Regression-first checks reproduced the faults before implementation: the component
suite had three failing new outcome cases, and the two operation-aware backend
variants failed because receipts were absent. The focused post-fix CVE suite passed
38 cases, and the component suite passed 33 cases.

An initial broad run exposed four incorrect empty-body test requests missing the
already-required JSON media type; the existing 415 guard was retained. Initial
seeded browser cases also used the wrong old first-lookup button label; they now
target the stable lookup action and assert it is visible/enabled. These were test
setup corrections, not removed application security or weakened assertions.

Final verification:

- `.test-artifacts/checks-e93bcb1f2a/`: **919 Python passed**, five Windows
  link-privilege skips, 150 opt-in cases deselected; **268 JavaScript passed**,
  all 28 syntax checks, lint and 188-file formatting passed.
- `.test-artifacts/f1f2-browser-confirm-20261018/`: **seven browser cases passed**.
  Chromium CVE cases cover old records, unrelated newer annotations, lost responses,
  matching receipts, unchanged-date cache recovery and reload without an automatic
  lookup. The Chromium library journey forces identical name timestamps/content
  and checks completion, newer notes and focus. Response-policy cases exercise
  Chromium and Firefox. This is not every functional flow in every engine.
- `.test-artifacts/f1f2-confirm-20261018/`: **38 focused CVE backend cases passed**;
  the component suite separately passed **33 cases** before the full gate.
- `.test-artifacts/package-ed88f4e5fa/`: installed wheel/dependency checks, seven
  page routes, 30 assets and synthetic report create/reopen/delete/Undo passed,
  using cached dependency wheels only. The runtime environment was not replaced.
- `.test-artifacts/live-review-20261018-b/verification-ac152b1d91/`: existing
  Light/Deep reports passed 320/390/768/1440-pixel, private export and device-library
  navigation checks, with no page errors or overflow and **zero scan submissions**.
  Saved test evidence and normal existing reports remained byte-for-byte unchanged;
  the owned verification backend stopped. No live refresh/analysis-navigation pass
  is claimed by this saved-only reopening.

Earlier failing artifacts are retained in `f1f2-before-20261018`,
`checks-22b983cdb9` and `f1f2-browser-20261018`, rather than represented as passing
first attempts. No fresh full browser matrix, hosted CI, real model generation or
live-device scan pass is implied by the targeted checks.

Repeat the offline gate with:

```powershell
.\.venv-quality\Scripts\python.exe -B scripts/check.py
```

For the targeted synthetic browsers, set `RUN_BROWSER_TESTS=1`,
`RESPONSIVE_BROWSERS=chromium,firefox` and `UI_UX_BROWSERS=chromium,firefox`, then
run `python -B -m pytest tests/browser_test_cves.py tests/browser_test_library.py
tests/browser_test_response_headers.py` with a new `--basetemp` and pytest
`cache_dir` below `.test-artifacts/`. Use the quality environment with browser
binaries already installed, not the runtime-only environment. Package verification
uses `scripts/check_package.py --offline --wheelhouse
.test-artifacts/home-review-20261008-wheelhouse`; that cached wheelhouse is local
test data, not part of a Git clone. None of these commands starts real scans.

## Handoff

Finish active scans, restart **NetGuard: Start backend**, then reload the report
tabs (Ctrl+F5) for the receipt API and browser modules to agree. Do not stop an
unrelated backend automatically. No commit, push, user-report deletion, database
migration, Pi-hole deployment or wider recommendation was performed.
