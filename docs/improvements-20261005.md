# Reliability and report improvements — 5 October 2026

## Implementation

1. **Bounded subprocess cleanup.** Scanner output uses the public asyncio
   subprocess protocol/transport API, separating process exit from pipe closure.
   A descendant retaining stdout can no longer make timeout cleanup wait
   indefinitely. Output limits, partial evidence, cancellation and failure flags
   are preserved. Windows cleanup closes owned pipes and stops the direct child;
   it does not promise termination of arbitrary descendant processes.
2. **Recoverable report notes.** Invalid or missing primary annotations recover
   from a validated previous copy under the scan lock. Corrupt primary bytes are
   retained in a uniquely named quarantine file and included in offline exports.
   Recovery advances the revision, rejects stale title edits and shows a warning
   that recent notes might be missing. Two invalid copies fail explicitly; they
   never silently become empty notes. Original scan evidence is not changed.
3. **Honest waiting information.** Progress responses include current backend
   contact and scanner-process lifecycle activity. The dashboard distinguishes a
   running check from time between checks. These are not completion estimates or
   proof that a remote device is responding.
4. **Shorter mobile reports.** Device details start collapsed on narrow screens,
   retain expansion state during rendering and remain keyboard accessible.
   Coverage cautions stay in the visible summary. Section links help readers jump
   between the overview, review items, devices and next steps. Extra explanation
   and mDNS advertisements use expandable sections without removing evidence.
5. **Evidence-based device roles.** The saved network snapshot can identify the
   scan computer and recorded gateway. These labels do not invent hostnames or
   imply a verified device identity. Complete reports label extra information
   “Scan notes”, without suggesting unfinished checks when there are none.
6. **Windows runtime diagnostics.** A scoped observer records the timestamp,
   exception type, Windows error code and callback name for event-loop errors.
   It delegates errors to the original handler and never suppresses them. The
   added diagnostic record excludes request arguments, session tokens and peer
   addresses; the existing default traceback remains unchanged.

The previous Windows connection-reset traceback was investigated against the
installed Python runtime. A deterministic test demonstrates that socket shutdown
can raise before the runtime closes that socket. This is **diagnosed, not repaired**
by the observer. No Python monkeypatch or runtime upgrade was applied.

## Verification completed before live testing

- Full regression: **442 Python tests passed**, one real-provider test deselected;
  no warnings. **53 JavaScript tests passed**.
- Chromium, Firefox and WebKit workflows passed, including responsive layouts,
  keyboard expansion and report-section navigation.
- Lint/format checks passed for 123 Python files; syntax checks passed for nine
  JavaScript files. Artifact directory: `.test-artifacts/checks-40a0708029/`.
- Real installed Nmap version command succeeded through the new process runner:
  **7.991**, exit code zero, no timeout or output overflow.
- An isolated preview of the previous seven-device Light report at 390 px reduced
  full-page height from 11,058 to 7,987 px (27.8%). No browser errors or scan POSTs.
  This is a layout measurement, not a nontechnical-reader usability study.

## Fresh live verification

Isolated backend on port 8766, Light on the freshly verified home
range `192.168.0.0/24`, then Deep on this Windows computer (`192.168.0.216`).
Artifacts: `.test-artifacts/improvements-live-20261005/`. Normal report storage
and the normal backend are not used for these test writes. External CVE lookups
are excluded; Pi-hole remains deferred.

Light `4c24df27-d061-4158-8897-dd975da6a903` finished in **230.5 seconds** with
9 checked devices of 10 discovered, 12 open services and eight review items. Device
`192.168.0.154` was unreachable on both attempts; Nmap returned a host-unreachable
observation rather than a process crash. Its cause is not established. The report
correctly says “Scan finished; 1 device could not be checked”, retains the failed
coverage and offers a retry. All nine AI records were ready. Refresh, history
reopen and 320/390/768/1440 px checks passed without browser errors.
A fresh 390 px load also confirmed ten initially collapsed entries (including the
unreachable device), keyboard expansion, section navigation and zero extra scan
submissions. Its collapsed page height was 8,625 px. The resize-after-desktop
capture retains already expanded cards; it is not the fresh-mobile default.
The first supplemental probe incorrectly expected the launch button to be enabled
during an active scan; the corrected read-only report probe passed. This was a
test-harness assumption, not an application failure.

Deep `d608fc7b-2e9c-4fa2-aced-732e8e7c22b4` completed on its first attempt in
**540.9 seconds**, with one checked device, 15 open services, four informational
review items and no scan errors. Its single limitation note correctly explains
that self-scanning does not prove what another device can reach. A separate read-only
progress probe confirmed a live backend timestamp and one running scanner check.
The live mobile progress page also displayed the new activity message with no
extra scan submissions or page errors.

Saved XML replay matched **135 Light / 22 Deep service-state records** and **8 / 4
findings**. All **14 AI records** revalidated, with no rejected fields or fallback
reasons; structured inputs contained no device IP addresses, MACs, hostnames or
raw XML. This verifies evidence consistency, not a comprehension study. The Light
report obtained two current mDNS names; Deep obtained a reverse-DNS name. These
remain unverified observations. The isolated folder has no historical nicknames.

Both profiles passed refresh, history reopen and four viewport widths, with no
page errors. Light Run again and both Deep choices returned to setup without new
scan submissions. Four Light services were eligible for CVE research; no external
lookup was performed. Deep had no eligible fingerprint, which is not a claim of
no vulnerabilities. The backend stderr contained no exception tracebacks in this
run; the earlier Windows reset did not recur, but is not proven fixed. The owned
test backend was stopped after all jobs finished. Normal storage/backend were not
modified; restart the normal task when idle to load the updated Python code.

## Remaining UI issue observed during the live check

At 390 px, the progress percentage renders `0` and `%` on separate lines. The
progress note also includes “scanner-check lifecycle event”, which is too technical
for the intended audience. These do not interrupt scanning. Recommended follow-up:
keep the percentage together and replace the lifecycle phrase with concise wording
such as “This check started 6 minutes ago”, retaining the distinction between app
contact, scanner activity and actual device responses. Evidence:
`.test-artifacts/improvements-live-20261005/deep-progress-mobile.png`.

## Further recommendations from the report review

- Keep the explicit failed-device count and retry workflow. A device appearing
  during discovery does not guarantee it will answer later checks; do not hide
  incomplete coverage to make the report look successful.
- Show recorded device roles alongside the first suggested action as well as in
  the device cards. For example, the saved gateway role can help a reader locate
  an unnamed router without claiming that its identity is verified.
- Continue reducing repeated cautions and technical terms, while preserving one
  clear limitation at each decision point. Test the wording with nontechnical
  readers instead of treating validated AI output as proof of comprehension.
- Investigate a supported Python/runtime solution for the Windows shutdown reset;
  keep the diagnostic and regression evidence, and do not suppress all resets.
- Verify the runner and network safeguards on the intended Ubuntu lab and the
  mobile layout on real phones. Browser emulation is not physical-device testing.
