# Device-first experience and focused assessment — execution plan

Requested on 14 October 2026. Implement presentation first, then scanning changes,
then a fresh authorised Light/this-PC Deep pair. Preserve local JSON storage,
original evidence, current recoverable deletion and bounded report pagination.

## Phase A — user experience

1. Add My devices: a rebuildable, bounded inventory from finished live reports.
   Group only unique usable adapter addresses on the same network; an IP alone
   cannot establish identity. Missing/ambiguous identities remain separate.
2. Save optional room, favourite and recognition annotations separately from facts.
   Require authenticated/CSRF writes, revisions, locks, atomic JSON and backups.
   Show first/latest recorded observations and links, never an invented live status.
3. Promote compatible comparisons into a What changed section, including source
   dates, added/not-observed features and explicit unavailable reasons. Old reports
   remain readable; do not mistake missing comparison metadata for no changes.
4. Add Unnamed devices/Unfinished checks shortcuts and a Need help task shortcut.
   Existing searches and priorities remain; show filter state and an easy reset.
5. Add an optional Features view over existing answering services, grouped in
   familiar language. Preserve inferred identification and incomplete coverage.
6. Add a printable/CSV summary with a privacy preview. Default identifiers and
   notes off; do not leak them through prose. Preserve coverage, dates, evidence
   qualifications, AI provenance and personal review status (not verified fixes).
7. Verify focused Python/JS tests and synthetic browser interactions/reflow, then
   the complete offline gate and packaged assets. No live work during this phase.

## Phase B — scanning improvements

1. Add bounded Deep-only SMB protocol/signing discovery via the explicit Nmap
   `smb-protocols` and `smb2-security-mode` allowlist entries. Parse complete,
   unambiguous evidence into specific SMBv1/signing review items, with sources,
   limits and reviewed plain-language/AI alternatives. No exploit or credentials.
2. Keep Light's existing small port set. The expanded Deep check contract must be
   versioned; do not compare old and new profiles as identical coverage.
3. Add opt-in local periodic Light checks and a quiet local event record. Off by
   default; require explicit scope authorisation and a verified home connection.
   Reuse existing validated scan submission/admission rather than bypassing guards.
   No new work while another job runs; no catch-up burst after sleep/restart; halt
   on a changed/unverifiable connection. Expose Pause/Stop and last outcome. This is
   app-running periodic checking, not a promised always-on protection service.
4. Test parser/rules/AI/fallback, failed/missing/truncated output, old JSON, deadline
   handling, scheduling/scope/sleep/overlap and notification deduplication offline.
5. Finish the full offline gate and package check before live traffic. Verify the
   current adapter; ask for authorisation if scope differs from the confirmed home
   range. Fresh isolated Light + Deep on this PC only, with normal reports untouched.
   Replay saved XML/rules and validate AI output; record failed host checks honestly.

## Deliberately excluded

No Pi-hole setup, remote control, automatic blocking, password guessing, packet
capture, arbitrary NSE categories, internet exposure tests, new IPv6 scanning or
intrusive TLS cipher enumeration. These were constraints/different product scopes
in the comparison, not approved default additions. A physical topology diagram
requires actual relationship evidence; unknown names are not intruder verdicts.

## Evidence to append

Record each implemented item, test command/artifact and actual result. Separate
synthetic checks, real Ollama, real browser views, live network and pending physical
phone/screen-reader/novice-reader testing. Do not claim all defects absent.

## Implemented and verified before live traffic

Phase A is implemented: My devices and household labels; first/latest included
observations and report links; explicit ledger-only unfinished records; structured
compatible comparisons; device/task shortcuts; feature-centric responses; a
private print/PDF preview and CSV export. Labels have revision fences and private
backup coverage. Print media hides the underlying identifying report. Original
guidance stays in evidence/technical export, not repeated in the default preview.

The UI-only gate `.test-artifacts/checks-c948eb6cce/` passed 724 Python tests, five
Windows link-privilege skips and the then-current JavaScript suites. Earlier gates
caught a missing new-page asset fixture, missing imports in the stripped-import
DOM harness and a missing legacy protocol fallback; these were corrected, not
treated as successful runs. Report browser cases passed eight Chromium/Firefox
cases; the independent device-library matrix passed six, including 320-pixel
reflow, stale edits, unreadable metadata and ledger-only results.

Phase B implementation adds Deep-only SMB protocol/signing checks and R08/R09,
ruleset 1.3.0 and reviewed prompt 4.4.0. Deep's public profile name remains
`deep-tcp-v1`; coverage ID is `deep-tcp65535-udp25-smb-v2`. Light is unchanged.
The installed Nmap includes both scripts; parsing matches its recorded strings.
Signing applies to the negotiated version only. Missing/truncated/conflicting
evidence yields no configuration finding. Recorded host replies, including
required-signing replies without a finding, are accessible once per device.

Optional periodic Light checking is off by default. Permission/scope are explicit,
connection approval is in memory, restart pauses stored schedules, and manual/AI
jobs block periodic admission atomically. Sleep delays defer rather than replay;
connection changes pause; submission/shutdown are bounded. Events are local and
deduplicated. Monitoring JSON and household labels are included in private backups.
It is not an always-on service or a promise of verified device security.

The combined gate `.test-artifacts/checks-5204b7abf9/` passed 816 Python tests,
six actual Windows link-privilege skips, 104 browser/provider/study deselections,
233 JavaScript tests, Ruff/174-file formatting and 27 shipped syntax checks.
The latest added monitoring browser file was excluded from that gate; its six
cases passed in the final browser matrix below. Offline package
`.test-artifacts/package-b7cb83f6a3/` passed
seven pages, 29 static assets, inventory/export/monitoring API smoke checks and
synthetic report removal/recovery, with clean build/runtime dependency checks.

An approval-service usage-limit failure stopped one browser command before it ran;
it was not a safety decision and was not bypassed. After resumption the approved
offline monitoring command ran: 40 passed/one Windows link-privilege skip. Its
synthetic Pydantic fixture warnings were subsequently removed. Monitoring UI tests
also cover rejecting an unchanged revision or mismatched enabled-state receipt.

The final Chromium/Firefox matrix
`.test-artifacts/competitive-browsers-20261014-c/results.xml` passed all 58 cases
with zero failures/errors/skips, including periodic permission/Stop/conflict,
privacy preview/print isolation, device labels/history, Delete/Undo/Restore,
Settings and appearance/reflow. Final formatting checks cover 175 Python files.
All 114 installed application files matched source byte-for-byte.

Fresh live pair `.test-artifacts/live-review-20261014-e/` started only after these
checks, on the verified home range `192.168.0.0/24` and this PC `192.168.0.216`.
The normal backend's public schema lacks inventory/share/monitoring endpoints,
although served assets are current. It was not stopped or restarted: finish
active work, restart that backend task and reload for the new Python routes.
The test used a separate owned backend/data folder. Pi-hole, NVD and periodic
checking stayed off. Completion/audit/cleanup evidence follows.
Real screen-reader/physical-phone and nontechnical participant evaluation remain
unverified; WebKit remains blocked by Windows policy.

## Fresh live results and final evidence audit

Both jobs ran through the browser against the new isolated backend and finished,
including local Ollama analysis, without scan errors:

- Light `1fc727c8-0939-4ed7-8e45-c4fd70a9441c`: 301.7 seconds, eight discovered
  devices/eight completed device checks, twelve answering features, eight review
  items (four low priority/four informational), no warnings or failed checks.
- This-PC Deep `280d0003-a9b5-4617-8bf9-7e9845456be0`: 525.8 seconds, one selected
  device/one completed check, fourteen answering features and four informational
  review items. Its one warning is the expected `SELF_SCAN_LOCAL_ROUTING`: these
  replies do not establish access from another device or the internet.

Deep saved complete `smb-protocols` and `smb2-security-mode` host output. The
protocol reply listed 2.0.2, 2.1, 3.0, 3.0.2 and 3.1.1; the 3.1.1 negotiation
reported “Message signing enabled and required.” Neither R08 nor R09 was raised.
This is evidence from those negotiations, not a universal safety, firewall or
all-version signing claim. Both host replies remain available in device supporting
details, even without an associated finding. Light retained its original six-script
allowlist; it did not receive the new Deep SMB checks.

The read-only audit command completed successfully:

```powershell
.venv-quality\Scripts\python.exe -B scripts/audit_live_review.py .test-artifacts/live-review-20261014-e
```

All 141 recorded service rows (120 Light/21 Deep), twelve deterministic findings
and the saved host-script output matched replay of retained Nmap XML. No raw host
file was missing. Thirteen accepted explanation records, including both overviews,
revalidated against the reviewed factual choices with zero rejected fields. One
Light informational item retained its plain-language fallback with reason
`not_simpler`; it was not the overview. Fourteen explanation records in total were
finished. Both reports recorded Ollama `llama3.2:3b`, prompt 4.4.0, and AI inputs
contained no recorded IP, MAC, hostname or raw scanner XML. These checks establish
the constrained wording contract, not measured comprehension by human readers.

`browser-results.json` records exactly two scan submissions, refresh retaining
both jobs, automatic report navigation after analysis, and no page errors or
horizontal overflow in the eight actual Chromium report/profile viewport checks
(320, 390, 768 and 1440 pixels). `feature-verification.json` confirms comparison
and feature sections, two private export previews, nine saved inventory records
without warnings and monitoring disabled. Nine records are not a claim of nine
distinct physical devices: ambiguous identities intentionally remain separate.
In this fresh isolated store Light recorded one named device through mDNS; Deep
recorded this PC's reverse-DNS name. Previous names/household labels were not copied
into the test folder. Unknown names and missing compatible comparisons remain
qualified; neither is presented as a threat or a claim that nothing changed.

`integrity.json` confirms all pre-existing normal reports remained byte-identical.
`cleanup.json` confirms the owned test backend stopped; a final read-only check
found no test listener on port 43144 and neither owned process (19412/25564).
The normal backend was left running. Final Ruff, 175-file formatting and
`git diff --check` passed; Git's CRLF conversion warnings were not code failures.

## Reading review and remaining follow-ups

The rendered reports explain a service as an answering device feature, put the
first practical action near the top, distinguish observations from security
verdicts, and warn before entering information on an unprotected device page.
The self-scan caveat is visible before Deep's findings. Technical acronyms and raw
SMB output are supporting evidence rather than the main instruction. The original
rule-based wording is not repeated as a second default explanation.

There are still worthwhile evaluation/improvement tasks, not failures concealed by
the passing gate:

- Test task completion and comprehension with nontechnical readers, including
  whether “review only,” “feature” and the HTTP/HTTPS advice need better examples.
- Run actual assistive-technology and physical-phone evaluation. Automated
  keyboard, themes, print privacy and reflow checks are not WCAG certification.
- Measure progress expectations on slower hardware: this pair took about five
  minutes Light and nine minutes Deep including AI. Do not promise fixed durations.
- Evaluate names across repeat authorised scans before relaxing identity rules.
  Sleeping devices, missing names and new observations are not intruder verdicts.
- Periodic scheduling/admission was tested with isolated synthetic data; this live
  pair only verified it remained off. A separately authorised, timed home trial is
  still needed before claiming real periodic execution verified.

Deployment hand-off: finish active jobs, restart the normal backend task and reload
the browser. Its pre-restart schema did not contain the new inventory, private-share
or monitoring APIs, although the static assets matched. Do not diagnose those old
process routes as a completed deployment of this implementation.
