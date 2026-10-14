# Second comparison, implementation and verification — 14 October 2026

Continue from the completed [first round](competitive-improvements-20261014.md).
Preserve its implementation, local JSON, raw evidence, recovery and bounded pages.
Research is a feature comparison, not a claim of product parity or certification.

## Current primary-source comparison

- [Fing device inventory](https://help.fing.com/hc/en-us/articles/14556062258204-Create-or-View-a-Device-Inventory)
  documents household locations, important-device flags and filtering. NetGuard
  already has separate room/favourite/recognition labels, but no explicit views
  using them. Adopt whole-inventory task filters, not an unverified online status.
- [Angry IP Scanner documentation](https://angryip.org/documentation/) describes
  reverse-DNS, NetBIOS, MAC, selected-port and version fetchers. NetGuard already
  implements related bounded naming and service checks. Do not add redundant name
  probes, broad ports or user-account collection just for feature count.
- [Greenbone reports](https://docs.greenbone.net/GSM-Manual/gos-24.10/en/reports.html)
  distinguish report presentation/export, evidence and filtering. NetGuard is not
  its authenticated vulnerability scanner/feed. Prefer reliable evidence and
  qualified results over copying an enterprise dashboard or inventing risk scores.
- [Nmap ssl-cert](https://nmap.org/nsedoc/scripts/ssl-cert.html) documents reported
  certificate start/end dates. Inspection found NetGuard compares an end date with
  the current clock and ignores a future start date, truncated output and duplicate
  date lines. Interpret the complete recorded period against the service check's
  recorded time instead; do not equate date validity with certificate trust.
- [NN/g filter application](https://www.nngroup.com/articles/applying-filters/)
  supports choosing deliberate filter application to fit the task. Keep one native
  labelled view selector in the existing search form, apply with Search, show the
  applied view and a reset, and filter before pagination.
- [W3C control labels](https://www.w3.org/WAI/tutorials/forms/labels/) and
  [form notifications](https://www.w3.org/WAI/tutorials/forms/notifications/)
  support visible labels, keyboard operation and clear success/error feedback.
  Preserve drafts and old evidence on failed requests; a missing server route must
  explain how to recover rather than present a generic failure.

## Executable scope and order

1. UI/API: My devices views All, Favourites, Not marked recognised, Unfinished
   checks and With review items. Intersect search before the 24-record page slice.
   Return the applied view; reject unsupported/stale filter responses. If saved
   household labels are unreadable, label-based views fail explicitly rather than
   treating everyone as unrecognised. Old unfiltered clients keep working.
2. Save reliability: accept household-label writes only with an increased revision
   and labels matching the submitted normalised draft. Keep draft/reload-required
   state on uncertain or contradictory receipts. Do not retry a write automatically.
3. Scan interpretation: use saved complete ssl-cert dates and service timestamp;
   explain expired, not-yet-valid or within-date-window in everyday language. Missing,
   invalid, truncated, error or ambiguous evidence yields unavailable, never a pass.
   Preserve raw evidence and existing risk priorities. No new probes; both Light and
   Deep benefit through their shared enrichment path. Version new enrichment.
4. Add focused Python/JS/browser regressions for server-side filters, paging, draft
   preservation, failed metadata/receipts, legacy backend and certificate edge cases.
   Run the full offline gate, Chromium/Firefox matrix and installed-package check.
5. Read-only network preflight, then only the authorised home Light and this-PC Deep
   pair in a new ignored isolated folder. If scope changed, request authorisation
   before sending probes. Do not enable schedules/Pi-hole/external CVE lookups.
6. Replay XML/rules and validate actual AI output; review rendered reports at narrow
   and wide sizes, retain refresh/no-duplicate-submission checks, verify existing
   normal reports unchanged and stop only the owned test backend. Record exact
   outcomes and unverified real-reader/physical-device/AT work here.

## Verification log

Implementation and results are recorded below; earlier round's passes are not
counted as verification of this round. No normal reports were deleted.

Implemented all three scoped changes. The shared certificate interpreter is pure;
it preserves endpoint script output and records missing/ambiguous/truncated/error
evidence as unavailable. It handles future start dates, date boundaries and UTC
normalisation, using the saved timestamp even for long-expired historical reports.
The risk rules, port sets and script allowlists are unchanged.

The focused offline regression run passed all 103 cases. The full gate in
`.test-artifacts/checks-5982233ea5/` passed 846 Python tests, six actual Windows
link-privilege skips, 112 browser/provider/study deselections, 237 JavaScript tests,
Ruff, 177-file formatting and 27 shipped syntax checks. Initial long-line lint
failures were fixed by formatting, not omitted from the record. After extending
the verification helpers, their final Ruff/format checks also passed.

The offline wheel check `.test-artifacts/package-0642df1c8b/` passed seven pages,
29 static assets, synthetic API/report recovery and both dependency checks. It used
the existing local wheelhouse, not downloaded upgrades or the normal app environment.

The first browser command failed during fixture setup because its nested artifact
parent directory did not yet exist; no browser case ran. The corrected matrix in
`.test-artifacts/competitive-round2-browsers-20261014-b/` then exposed two old
empty-message assertions, one per engine. The new message correctly includes the
applied view; those expectations were updated. Final results appear below.

The complete ten-case affected inventory retest
`.test-artifacts/competitive-round2-inventory-retest-20261014-a/results.xml` passed
in both Chromium and Firefox (zero failures/errors/skips). It covers deliberate
whole-library views, reset/empty feedback, legacy-backend draft retention, existing
revision conflicts, readable observations during metadata failure and 320-pixel
reflow. All 115 installed application files matched source byte-for-byte. Final
Ruff, 177-file formatting and normal `git diff --check` passed. Windows line-ending
conversion warnings are not changes to the evidence or product failures.

Read-only preflight still detected the previously authorised home range
`192.168.0.0/24`, this PC `192.168.0.216`, and the same routed connection. No
additional network authorisation is inferred for a different range or device.

The wider browser matrix finished with 60 passes and only the two known stale-text
assertions. Both affected cases passed in the ten-case inventory retest, so all 62
distinct selected cases have passing coverage across the final matrix/retest;
this is not reported as a single clean 62-case run. No browser regression started
Nmap or contacted a real device.

The fresh pair began in `.test-artifacts/live-review-20261014-f/` only after those
checks. Its preflight found the normal server now has the first-round inventory,
share and monitoring APIs, but not the new device-view query contract. Served
assets match source. A backend restart after active jobs finish remains necessary
for this round; the isolated test backend loads the new implementation directly.
The fresh live completion, replay/AI audit, normal-data integrity and cleanup
results follow.

## Fresh live results

- Light `2ea4a539-d663-4664-8ee4-f14b3ce826a0`: 317.7 seconds including AI, eleven
  discovered addresses, ten completed device checks, twelve answering features
  and eight review items (four low/four informational). One address could not be
  reached after two bounded attempts (`HOST_UNREACHABLE`); the cause was not
  established. It is not counted as checked or diagnosed as asleep. The page says
  **“Scan finished; 1 device could not be checked.”** Its coverage, overview and
  retry action retain that limitation. State `partial` remains truthful in JSON.
- This-PC Deep `80d107ff-fb68-4250-8e25-08b5246f8d68`: 527.3 seconds including AI,
  one selected/completed device, fourteen answering features and four informational
  review items. No scan errors. Its expected `SELF_SCAN_LOCAL_ROUTING` warning
  remains visible: this does not establish access through the firewall from other
  devices or the internet.

The read-only command below passed:

```powershell
.venv-quality\Scripts\python.exe -B scripts/audit_live_review.py .test-artifacts/live-review-20261014-f
```

All 171 service rows (150 Light/21 Deep), twelve deterministic findings and saved
host-script replies matched raw XML replay for completed checks. No completed
host's raw file was missing. Two actual Light certificate explanations revalidated
against their raw dates and saved check timestamps, with neither detail omitted.
Both were within their recorded date windows, explicitly not a trust/safety pass.
Deep returned no certificate-date script result, so it is not described as a live
certificate test; the shared path and invalid/future/expired boundaries are covered
by the 29 focused synthetic certificate cases. The existing Deep SMB negotiation
checks still recorded modern dialects and required signing for the negotiated
version; no new SMB finding was invented.

Thirteen accepted explanation records, including both overviews, revalidated with
zero rejected fields. One other Light item kept a recorded `not_simpler` fallback;
all fourteen explanation records finished. Both used local Ollama `llama3.2:3b`
and prompt 4.4.0. The AI inputs contained no recorded IP/MAC/hostname or raw XML.
The Light overview explicitly says ten checks finished/one could not finish and
suggests retrying unfinished checks. This is validation of constrained wording,
not proof of comprehension by all readers.

`browser-results.json` confirms no page errors or horizontal page overflow in
eight actual Chromium profile/viewport checks (320/390/768/1440 pixels), exactly
two scan submissions, refresh retaining both jobs, and navigation after analysis.
`feature-verification.json` confirms both private previews, comparison/feature
sections and live inventory view/reset interactions. The twelve inventory records
include an unmatched unfinished address and separately qualified identities, not
a claim of twelve distinct physical devices. Filter totals: zero favourites,
twelve not marked recognised, one unfinished, six with review items. No household
labels were copied into this fresh store. There were no inventory warnings, and
periodic checking stayed disabled. Light recorded two mDNS names; Deep recorded
this PC's reverse-DNS name. No names were invented to fill missing identities.

`integrity.json` confirms all pre-existing normal reports stayed byte-identical.
`cleanup.json` confirms the owned test backend stopped. A final read-only process/
listener check confirmed no owned process (46240/34000) or listener on port 19749.
The normal backend was not restarted or stopped. Final lint/format/diff evidence is
recorded above; no application source changed after the verified package build.

Deployment: let active jobs finish, restart the normal backend task, then reload.
The running normal process has the earlier APIs but does not yet advertise the
new `view` query. The UI detects that mismatch instead of silently showing an
unfiltered collection. The isolated live reports remain in their ignored artifact
folder, not the user's normal Saved reports library.

## Remaining improvements, not automatically enabled

- Evaluate the new views and certificate wording with nontechnical readers rather
  than claiming automated checks prove comprehension. Observe whether recognition
  labels are confused with safety results and whether reset is easy to find.
- Actual screen-reader speech, physical phones and Windows-blocked WebKit remain
  unverified. Keep native labels/focus/motion safeguards; do not claim certification.
- Continue evaluating device names over multiple authorised runs. Reused IPs,
  randomised adapter addresses and sleeping devices limit reliable matching; do
  not replace missing names with confident guesses.
- Consider an explicitly selected, endpoint-bound TLS trust/hostname check later,
  with a separate evidence contract. Certificate dates are not chain trust or
  hostname matching. Do not add aggressive cipher enumeration by default.
- Consider report-to-device return context and optional per-tab inventory view
  restoration after usability feedback. Never persist network scan permission as
  an incidental display preference.
- A timed periodic-check trial remains a separate authorised task; monitoring stays
  off in this live pair. No cloud accounts, remote control, Pi-hole installation,
  password checks or external CVE feed changes are part of this round.
