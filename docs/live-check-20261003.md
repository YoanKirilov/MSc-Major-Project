# Remediation live verification — 3 October 2026

Scope: normal local application and saved home reports; Light on the verified
authorised `192.168.0.0/24`, then Deep only on the freshly identified Sony
KD-50X75WL. Nmap 7.991; local Ollama 0.34.2 with llama3.2:3b. No Pi-hole deployment,
router change, SQLite migration or deletion of saved reports.

## Offline and installed-package checks

- 394 Python tests passed; one real-provider test deselected, one existing
  Starlette/httpx deprecation warning. 50 JavaScript tests passed, with browser
  checks in Chromium, Firefox and WebKit, Python lint/format and module syntax.
  Artifact: `.test-artifacts/checks-243fbcc4e8/`.
- The final AI queue checkpoint change additionally passed 16 focused tests.
- Final installed wheel passed six pages, ten static assets, demo read/create/reopen
  and dependency consistency: `.test-artifacts/package-5ce852931f/`.

## Live Light

Successful verification run: `c33bf095-4512-4851-8963-a1e592b8a6e7`, 310.8 seconds.
13 discovered devices; 11 checked, two unreachable after two attempts each.
12 open services and eight review items (four low, four informational).
This is **incomplete device coverage**, not a claim that all devices passed.
The report says "Scan finished; 2 devices could not be checked" and offers retry.

Retained XML replay matched all 165 service-state records and eight rule findings.
Ollama produced seven accepted records; two retained reviewed wording because the
alternative was not simpler. All accepted records revalidated; selected AI inputs
contained no device IP addresses, names, MAC addresses or raw XML.

Fresh mDNS identified the Sony and a MacBook. Unknown devices remained unknown;
advertisements were not treated as proof of service responses. Two unreachable
devices were recorded as `.54` and `.154`, without guessing why they did not answer.

Refresh and history reopening passed. No page errors or horizontal overflow at
320, 390, 768 and 1440 pixels. A separate saved-report check blocked external
requests and confirmed collapsed technical details, unfinished-check disclosure
and AI attribution. The 390-pixel first screen was visually reviewed: the main
outcome, plain explanation, incomplete checks and retry action were readable.
These are browser-emulated widths, not physical-phone usability certification.

## Live Deep

Sony job `89d7d58c-a1a2-4569-8d20-41c687c303b1` completed in 641.2 seconds on its
first attempt: one checked device, 15 open services, nine review items (two low,
seven informational), no scan warnings or errors. All ten AI records were accepted
and independently revalidated. XML replay matched all 30 stored service-state
records and nine rule findings. The limited scope remains explicit: this is not
proof that the television has no vulnerabilities.

Refresh, history reopening and 320/390/768/1440-pixel layouts passed without page
errors. Only two scan submissions were made in the successful verification run.
All 147 pre-existing scan JSON files checked by the integrity manifest were unchanged.
Run again passed for Light setup and both Deep same-device/another-device choices,
without submitting further scans. The verified idle backend was restarted after
the run to load the last fixes; both saved reports reopened and Nmap was available.

## Defect found and fixed during live verification

Initial Light `31f203bb-646b-4467-a3c0-309ba59e1715` failed because per-attempt XML
filenames introduced by retry diagnostics were rejected by storage's old filename
policy. The failed report remains saved. The bounded whitelist now accepts attempt
1/2; 45 focused supervisor/storage tests passed with raw retention enabled, followed
by the full regression and successful Light retry above.

The final navigation check also exposed a report-loading race: Run again was
initially enabled before its data arrived, so an early click could do nothing.
It now starts disabled and enables only after report loading; a static regression
and the live same-device/another-device navigation check protect this behaviour.

## CVE reference verification and privacy boundary

A synthetic public nginx 1.10.1 example resolved the old vendor identifier to one
dictionary candidate and returned 15 reference records in 27.09 seconds; five were
retained. Original/resolved identifiers and provenance were preserved. This is
reference research, not confirmation of vulnerability applicability.

The separate attempt to exercise the real saved home-device fingerprint through
the CVE button was blocked by automatic approval review before execution, because
it would disclose detected product/version information to external NVD. No such
home-device fingerprint was sent by that check. Explicit approval was requested;
local checks continued without it. Mocked browser tests cover the interaction.

## Remaining evaluation

Real-reader evaluation, physical-phone/assistive-technology sessions and an
authorised Ubuntu lab remain pending under `evaluation-remediation-20261003.md`.
Cross-platform raw-packet capability preflight needs lab validation; clear observed
permission/driver diagnostics do not prove every operating system is ready.
Network continuity checks are best effort, not atomic network isolation.

Artifacts: `.test-artifacts/live-remediation-20261003/` for live reports, timelines,
screenshots and replay; `.test-artifacts/remediation-20261003/` for the initial
failed run, focused checks and synthetic public CVE lookup.
