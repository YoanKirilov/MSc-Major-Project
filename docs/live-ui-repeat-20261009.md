# Repeated live scan and UI review — 9 October 2026

## Implementation addendum — 12 October 2026

The user authorised implementing the pending fixes and beginner-oriented UI
improvements below, followed by new authorised Light and this-PC Deep verification.
The original 9 October evidence and recommendations below remain historical records.

Execution order and acceptance checks:

1. Return helpful retryable responses for scan/progress storage-read failures.
   Keep missing/invalid reports and permission/lock errors distinct. Reload must
   preserve the scan ID and must not submit a new scan.
2. Match a complete valid device IPv4 address exactly in device/review searches
   and recognition shortcuts. Keep partial/text search; include unchecked addresses.
3. Replace unchecked-device zero previews with explicit “Not assessed” wording.
   Keep recorded partial observations distinct from checks that never finished.
4. **New request:** replace per-feature “Supporting feature details” controls with
   one disclosure per device, placed at the end beside “About this device”. Group
   evidence by feature, preserve every saved name/version/check output, and keep
   keyboard focus/disclosure state stable across refresh and nickname projections.
5. **New request:** make cards and feature rows more compact; use purpose-first
   headings, secondary technical context and short, ordinary-language explanations.
   Review as a complete computing beginner, not someone who already knows ports,
   protocols or software fingerprints. Do not turn uncertain observations into
   confirmed identities, vulnerabilities or safety claims.
6. **New request:** justify longer explanatory report paragraphs. Exempt headings,
   controls, short status/context text and technical evidence. Provide a left-aligned
   reading choice and verify narrow/enlarged layouts without changing saved facts.
7. Bring unfamiliar-term explanations, safe first-step precautions and cautious
   feature-specific decision aids into the reading flow. Add a guided identification
   path with explicit user-triggered naming/nickname actions; no automatic new probes.
8. Investigate the intermittent Windows connection-close callback using isolated
   loopback/subprocess checks and primary runtime sources. Do not monkey-patch private
   transport methods, suppress errors or switch to an event loop that cannot launch
   Nmap. If no supported safe fix is available, record that limitation explicitly.
9. Run focused and full offline/three-browser regressions, then isolated live Light
   and this-PC Deep scans if the confirmed home scope still matches. Replay raw XML,
   risk rules and AI validation; review novice wording and responsive/refresh/history/
   Run again behaviour. Preserve all original reports, record exact results and
   distinguish actual reader/physical-phone/lab work not performed.

Implementation status and new verification will be recorded in a separate dated
execution record; this addendum does not claim that any item has passed yet.

Update: [12 October implementation and verification](readability-fixes-20261012.md)
records the implemented application/UI changes and new live results. The Windows
transport investigation and actual-reader/physical-device work remain explicit
limitations; the original 9 October recommendations below are historical, not
the current implementation status.

Repeated the authorised Light home-network and this-PC Deep checks after
[the earlier review](live-ui-review-20261009.md). This is a verification and
recommendation record: no application-code fixes, dependency upgrades or deletions
were made. Pi-hole remains deferred; no real CVE-provider lookup ran.

## Scope and evidence protection

Windows and the app both detected `192.168.0.0/24`, with this PC at
`192.168.0.216`, matching the user's confirmed home scope. The final adapter check
still reported that address and prefix. No virtual-adapter network was scanned.

Exactly two scans were submitted through an authenticated owned backend on 8766.
Its fresh JSON directory was `.test-artifacts/live-ui-repeat-20261009-3d67d126/data/`.
The two completed reports from the earlier same-network review were copied unchanged
as a comparison baseline. The normal backend on 8765 was neither authenticated to
nor restarted. Normal reports, copied reports and reopened new evidence retained
their original hashes. Owned test/viewer processes were stopped; the final listener
check found the normal app on 8765 and no listener on 8766.

These new reports are isolated test evidence, not entries in normal app history.
The test folder did not copy the complete normal nickname/history library.

## Live results

| Measure | Light home network | Deep this PC |
| --- | --- | --- |
| Scan ID | `467b20cd-2d91-444a-93bc-ddd14a4ac9dc` | `99b1ddc7-458a-4e76-a6ce-0c301068604c` |
| Final result | Finished with incomplete coverage | Completed |
| Device checks | 9 completed of 10 discovered; 1 unreachable | 1 completed of 1 selected |
| Open features | 12 | 13 |
| Review items | 8: four Low, four informational | 4 informational |
| AI records, including overview | 8 ready; 1 retained reviewed guidance | 5 ready |
| Elapsed including report preparation | 318.8 s, about 5 min 19 s | 524.3 s, about 8 min 44 s |

Nmap 7.991, Python 3.14.2, Ollama `llama3.2:3b` and prompt 4.2.2 were used.
Light selected 12 TCP and three UDP ports per discovered device; Deep selected
all TCP ports and 25 UDP ports on this PC. Completion concerns those selected
checks, not every possible security setting or device on the network.

Light discovered `192.168.0.154`, but both bounded service-check attempts returned
`HOST_UNREACHABLE` (approximately two seconds each; Nmap exited normally).
That is a reachability limitation, not evidence of an application crash or an
intruder. Its physical cause was not established. The report correctly says
**“Scan finished; 1 device could not be checked.”**, offers retry, retains the
reason/attempts, and includes the address as an explicitly unchecked device card.
No retry button was pressed in the read-only review.

Deep had no scan errors. It retained the expected self-routing limitation: a program
answering on this PC does not establish access from another device or the internet.

Seven Light devices matched earlier observations by nonduplicated adapter address;
their comparable service observations showed no changes. Two earlier devices were
not matched this time, with sleep/disconnection/address-change uncertainty preserved.
Neither a match nor a difference establishes verified identity or an attack.

Light retained two mDNS announcements and one reported name; eight usable results
had no name. Deep recorded one reverse-DNS name. Four Light services were eligible
for optional precise-version CVE research; none in Deep were. Eligibility is not a
CVE match or a vulnerability verdict.

## Checks completed

- Retained host XML replay matched all **155 service records** and **12 findings**,
  excluding generated timestamps. Non-open states were not converted to open services.
- All **13 ready AI records** revalidated against their source-bound reviewed choices.
  There were no rejected fields. One Light R07 item recorded `not_simpler`: Ollama
  supplied no accepted clearer alternative, so reviewed guidance remains. This is
  not an AI outage. Its overview retained the unfinished-check warning.
- Reconstructed selected AI inputs contained no device or coverage IP/MAC/name
  identifiers, network CIDR or raw XML. Ollama selected validated wording; it did
  not add findings, alter priorities or invent remediation/CVE conclusions.
- Refresh during both running scans recovered progress and the fixed Deep target.
  Both pages automatically opened their reports after analysis, including the
  incomplete Light result. Only the two original scan submissions occurred.
- Read-only report reopening passed **16 engine/profile/viewport combinations**:
  Chromium at 320/390/768/1440 pixels; Firefox/WebKit at 390/1440. Mobile startup
  also rendered in all three. No page errors or horizontal page overflow occurred.
  Disclosure/selected-item reload recovery passed in each engine; Chromium also
  checked search recovery, history reopening, Light Run again and Deep Same device
  setup. Those setup actions submitted no scan or edit.
- Read the rendered overviews and all 12 review-item details, and visually checked
  mobile startup/detail captures. Failed-check and fallback-provenance assertions
  passed. All **16 static assets** matched source bytes and served with `no-store`.
- Fresh offline gate passed **582 Python tests and 102 JavaScript tests**, with 39
  browser/provider/lab/study cases deselected. Ruff lint/format passed for 143 files;
  all 15 JavaScript/module syntax checks passed. Artifacts: `.test-artifacts/checks-89165c37e3/`.
- Import traversal found all **67 application Python modules reachable**. Framework
  callbacks and public/tested helpers are not a safe deletion list. No unused-file
  removal or structural rewrite was justified by this repeat review.
- The isolated scan and viewer stderr logs contained no tracebacks, reset callbacks
  or ERROR entries this time. This does not establish that the earlier intermittent
  Windows transport issue has been fixed.

Final browser evidence: `.test-artifacts/live-ui-repeat-20261009-3d67d126/browser-check-655b0f68/`.
Timelines, reports, retained XML, preflight, AI/evidence replay and synthetic I/O
diagnostics are in the parent folder. Private bootstrap logs and identifying scan
artifacts must be sanitised before publication.

An intermediate viewer assertion mistakenly checked the hidden AI-outage notice
instead of the provenance field. It was corrected in the test harness only; the
final pass checked the actual field and that the outage notice stayed hidden.
The failed intermediate artifacts remain in `browser-check-a9a2639c/`; they are
not counted as a pass. No extra scans were submitted to repair that test assumption.

## Remaining faults and recommended execution order

1. **Storage-read recovery — confirmed, still pending.** Fresh isolated injection
   of `OSError` into scan/progress reads again returned generic HTTP 500 responses.
   Live storage succeeded. Add a consistent bounded 503/retry boundary, keeping
   missing/invalid and permission errors distinct, and preserve the pinned scan ID.
   Add API/frontend regressions; never submit a replacement scan automatically.
2. **Exact-IP search/recognition — reproduced, still pending.** This Light report's
   full `192.168.0.1` query matched three cards, including prefix addresses. General
   substring search is working as written, but a complete address/recognition
   shortcut should target one device. Retain partial/text search for other queries,
   and test prefix collisions, unchecked-device entries and refresh recovery.
3. **Unchecked-device numeric preview — newly observed presentation ambiguity.**
   The unreachable card clearly says its checks could not finish, but immediately
   shows `0 observed features · 0 review items`, like a completed empty result.
   Those counts are saved-observation counts, not evidence that no features exist.
   Prefer “Features not assessed; no usable check result” for an unchecked placeholder;
   retain any genuinely recorded partial observations separately. Test failed,
   timed-out/cancelled and completed-empty cards without changing scan evidence.
4. **Intermittent Windows socket-close callback — pending investigation.** The
   earlier review captured a transport `ConnectionResetError`, but this repeat did
   not. Keep the issue open; investigate a small supported-runtime reproduction
   instead of suppressing unrelated errors or patching private transport methods.

No additional live scanner/parser/rule/AI corruption was observed in this repeat.
The unreachable device must remain incomplete unless a later authorised check
actually finishes; changing the label must not mark unperformed checks passed.

## Plain-language and UI recommendations

The report is much clearer than raw scanner output: it defines services, separates
observations from safety claims, exposes coverage gaps, and gives useful Windows/
VMware and web-page directions. It is not yet proven understandable to everyone.

Next, reuse the existing glossary inline for unfamiliar terms; shorten repeated
protocol/port headings on mobile; give generic “check whether this connection is
expected” actions a cautious, device/feature-specific decision aid; put HTTP/password/
certificate precautions beside the short first action as well as detailed help;
and offer a guided identification/device-focused reading path. Keep original
evidence, uncertainty and task status accessible. These recommendations follow
[W3C clear-word guidance](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o3p01-clear-words/).

Finally, run the existing consent-based nontechnical-reader session and keyboard/
screen-reader/enlarged-text/physical-phone checks. This assistant's editorial review
and browser emulation are not comprehension measurements or WCAG certification;
see [W3C user-evaluation guidance](https://www.w3.org/WAI/test-evaluate/involving-users/)
and [the session kit](evaluation-session.md). Ubuntu/lab ground truth, real Pi-hole
and real CVE-provider behaviour were not verified by this repeat.
