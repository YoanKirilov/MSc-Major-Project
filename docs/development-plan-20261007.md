# Development plan — 7 October 2026

Source: `architecture-live-review-20261007.md`. Implement in the order below. Keep JSON storage, saved scan evidence, permission checks, five-slot scan concurrency and the current visual style. Do not deploy Pi-hole, upgrade Python, contact vulnerability providers or change the user's running backend as part of this work.

## 1. Nickname reliability

- Return readable 503 errors for unavailable nickname storage and 409 for unreadable/conflicting edits; keep missing reports/devices as 404.
- Load and recover nicknames under the same cross-process lock used for edits. Validate the previous backup before restoring, preserve corrupt primary bytes for investigation, invalidate stale editors and disclose potentially lost latest edits.
- Never silently reset unreadable data, replace unsafe paths, recover oversized data automatically or alter original scan observations/identity anchors.
- Tests: failed reads/writes, corrupt/missing primary, invalid backup, stale revision, concurrent writers, size/path boundaries and unchanged scan evidence.
- During execution, also reproduce and fix the same repeat-recovery revision reuse
  in report notes; share the small revision-reservation helper and retain separate locks.

## 2. Active Deep scan experience

- Restore the immutable target on refresh, disable launch/setup controls while running and promote progress on small screens without scrolling on every poll.
- Preserve independent Light/Deep pages, pinned report URLs and browser-storage failure handling.
- Tests: start and resume, mobile progress in the viewport, immutable target, no duplicate scan submission, and existing desktop layout.

## 3. Explicit input limits

- Apply one shared maximum of 254 selected Light addresses in both request validation and the standalone scope validator. Deep remains one address.
- Bound address, range, mode and profile text; retain RFC1918 scope checks and duplicate rejection.
- Tests: maximum/maximum-plus-one, malformed/long/non-string addresses, duplicate/out-of-scope addresses and broad administrator-configured scopes. No large live test.

## 4. Understandable reports

- Explain naming sources, earlier saved names and why an unnamed device is not automatically suspicious.
- Give recognised probed services readable labels without turning port-number guesses into verified software identities. Make first actions appropriate for the computer that ran the scan.
- Add a separate bounded earlier-observations view only when comparison is meaningful; do not turn absence into a security finding or unfinished checks into completed checks.
- Tests: source/confidence wording, safe rendering, identity ambiguity, scope/time/profile limits, incomplete coverage and unchanged findings/severity.

## 5. Remaining evaluation work

- Retain non-suppressing Windows socket-reset diagnostics; run bounded local tests rather than claiming a runtime change fixes an unreproduced failure.
- Prepare a reader-study protocol; actual participants, physical-device accessibility and authorised Ubuntu testing remain manual work.

## 6. Verification and handoff

- Run focused regressions, all offline Python/JavaScript checks and Chromium/Firefox/WebKit responsive browser tests using isolated JSON folders.
- Record exact results and any unfinished or environment-dependent work in this file and `testing.md`. Do not imply mocked tests are live scans or participant research.
- A fresh live home-network verification is a separate optional final step, only after confirming the current network; Deep target is this Windows computer, not the sleeping Sony TV.
- Tell the user to restart the normal backend when idle to load backend changes; never terminate their existing scans.

## Execution record

Implemented steps 1–4. Step 5's bounded Windows diagnostic and updated reader protocol
are complete; the underlying intermittent reset and actual reader evaluation remain open.

- Nickname API reads/writes have explicit error boundaries, locked backup recovery,
  notices, bounded quarantine and revision protection. A dedicated failing regression
  also exposed repeat-recovery revision reuse in report notes; the shared
  `storage/recovery.py` guard now covers both. Backup export includes fences/quarantines.
- Deep/general-page refresh restores the recorded target, disables setup and moves
  progress ahead of setup once. Missing reports restore usable setup; temporary metadata
  outages keep the existing job pinned and prevent a duplicate launch.
- Request schema and core validator cap selected Light hosts at 254, bound text and
  reject non-string host inputs. No large-host network probe was run.
- Optional enrichment records up to 50 unmatched earlier observations from the newest
  compatible finished Light discovery report in the bounded recent-history set. Previous
  unfinished checks, unknown/zero/ambiguous adapter identities and currently observed
  addresses are excluded. Old reports are not rewritten/backfilled. Findings and AI input
  are unchanged. Naming coverage, VMware feature descriptions, shorter gateway labels
  and a scan-computer-specific first action improve the report's beginner presentation.
- Expanded the reader-session kit with progress/recovery/naming/comparison/self-scan tasks.

### Final verification

- Full gate passed: **515 Python tests, 65 JavaScript tests**, Ruff lint/format across
  131 Python files and ten module syntax checks. Chromium, Firefox and WebKit passed
  the eight-viewport responsive matrix; mobile active Light/Deep refresh, fixed targets,
  cancellation and independent tabs passed in each engine.
  Artifacts: `.test-artifacts/checks-3d5e261444/`.
- Final installed wheel passed from a fresh isolated environment: six pages, eleven
  static assets and demo create/read/reopen; dependency consistency passed. Artifacts:
  `.test-artifacts/package-fc70033dfa/`. The normal virtual environment was not upgraded.
- Final security gate passed: no known advisories in the pinned dependency audit,
  no medium/high static findings and no potential secrets. Fifteen low static findings
  remain in the evidence, not suppressed. Artifacts: `.test-artifacts/security-3dabd22a5e/`.
- Real local Ollama test on synthetic facts passed: source-bound output validated,
  saved, unchanged finding severity/actions and genuine simpler accepted meaning.
  This is not a comprehension study or a fresh network scan.
- Windows 3.14.2 Proactor probe passed eleven orderly/ten abrupt loopback disconnects,
  twenty concurrent harmless subprocesses and post-disconnect responsiveness; no
  diagnostic errors. The intermittent application reset was **not reproduced or fixed**.

Earlier failed/interrupted runs remain audit evidence. Obsolete frontend-version
assertions were corrected. The expanded Firefox test initially stalled during its
background-tab resize/refresh sequence; a diagnostic run isolated the sequence, and
setting the viewport before creating tabs/selecting the tab before refreshing allowed
both Firefox cases and the final complete matrix to pass. Only owned stalled test
processes/browser descendants were stopped, never the user's normal backend.

### Resume point / handoff

Implementation and automated verification are complete. Restart the normal backend
only when idle, then hard-reload the browser. Original reports, nicknames and the
running normal backend were not used for synthetic fault tests or replaced.
No fresh Nmap home-network scans were run in this implementation turn. The earlier
7 October live review tested the **pre-change** code; it is not new post-fix evidence.
Next: confirm the current authorised home network and run one Light scan and one
Deep scan on this Windows computer, inspect actual name/comparison coverage, and
replay XML/rules/AI validation. Keep Pi-hole deferred. Reader participants, actual
phones/assistive technology, Ubuntu live checks and any Windows-reset reproduction
remain explicitly pending.

### Post-restart follow-up

The subsequent authorised home-network repeat completed both actual scans with no
failed checks, and replayed all 14 real Ollama records successfully. Fresh full
regression again passed 515 Python/65 JavaScript tests and three browser engines.
Normal/copied reports were unchanged and the owned test backend was stopped.
See `postfix-live-review-20261007.md` for exact results and the two newly identified
frontend follow-ups (delayed nickname snapshot regression and naming-button wording).
These follow-ups are recorded, not implemented during the verification request.
