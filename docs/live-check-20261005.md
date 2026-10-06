# Live verification and code review — 5 October 2026

## Scope and safeguards

Verified Wi-Fi `192.168.0.216` and gateway `192.168.0.1` against the previously
authorised home subnet `192.168.0.0/24`. Light used that subnet; Deep targeted this
Windows computer, not the standby Sony. The test-owned backend used port 8766 and
`.test-artifacts/both-recheck-20261005/data`. Only settings were copied; normal
history, nicknames and session credentials were not imported or modified.

Nmap 7.991 and local Ollama `llama3.2:3b` were available. No device fingerprints
were submitted to an external CVE service. Full regression tests run after the
live jobs to avoid unnecessary load during this verification.

## Live results

- Light `9c89d1d1-b2b9-4ebd-9815-ecbac48ff932` completed in **210.8 seconds**:
  seven discovered devices, all seven checked, ten open services and seven review
  items (three low, four informational), with no errors or warnings.
- Deep `6ce9b969-9c50-47fb-a893-1f48a2a162a2` completed on its first attempt in
  **540.9 seconds**: one checked device, 14 open services and four informational
  review items, with no scan errors. Its single warning explains that a self-scan
  does not establish what another device can reach.

Light refresh, saved-history reopen and 320/390/768/1440-pixel viewport checks passed
without page errors. One device had a current mDNS name; unknown names remain
unknown. This isolated folder has no historical identity/nickname data, so its
name counts must not be compared directly with the populated normal app history.
Deep passed the same refresh/history/viewport checks and both Run again choices.
No extra scan was submitted during navigation. The owned backend was stopped
after it became idle; the normal backend was not restarted.

Saved XML replay matched all **105 Light / 21 Deep** service-state records and
**7 / 4** findings. All **8 Light / 5 Deep** AI records passed revalidation, with
no rejected fields or fallback records, and their structured inputs contained no
device IP, MAC or hostname. This verifies source consistency, not a usability
study or proof of complete vulnerability coverage. The name on the Deep device
came from reverse DNS and remains an observed, unverified label.

The earlier network-query interruption did not recur in either job. Full backend
stderr was not clean: it contains one `ConnectionResetError: [WinError 10054]`
from asyncio's Windows `_ProactorBasePipeTransport._call_connection_lost` callback.
No scan failure, lost report or browser error accompanied it. The trace does not
identify the connection or precise timing, so its origin has not been established.
Do not describe this run as having no exceptions anywhere.

## Code organisation

Removed the unused optional fallback branch from the private Windows adapter-query
function. The public wrapper remains the single place deciding whether to return
`None` or raise a structured diagnostic. Consolidated repeated network-message
imports in the supervisor. The scan backend had already loaded the pre-cleanup
code; this is a behaviour-preserving cleanup verified separately by regressions,
not a claim that a restarted live backend ran the refactored source.

Added six regression cases for malformed/oversized output, failed subprocesses and
startup errors, checking both public fallback and strict diagnostic behaviour.
Twenty-eight focused cleanup/structure tests passed. No application modules,
templates or static assets were identified as safely unused and deleted. Existing
uncommitted changes were preserved.

Final `scripts/check.py --browser --browser-engines chromium,firefox,webkit` passed
**433 Python tests**, one real-provider test deselected, **51 JavaScript tests**,
all three browser engines, lint/format for 121 Python files and nine JavaScript
syntax checks. Artifact: `.test-artifacts/checks-8d1f0e2b04/`. This includes the
post-startup cleanup. Reload the normal backend when idle to load pending changes;
the test server was deliberately separate, so these two reports are not in normal
history. Live evidence remains in `.test-artifacts/both-recheck-20261005/`.

## Recommended next improvements

1. **Investigate Windows connection-reset logging:** add timestamped connection/
   lifecycle diagnostics and a reproduction for orderly and abrupt client closes.
   Handle only verified expected disconnects; do not globally suppress connection
   errors or alter the network-safety guard to hide this traceback.
2. **Finish the two outstanding reliability items:** bounded output-pipe cleanup
   when a subprocess descendant retains a pipe, and validated annotations-backup
   recovery that preserves revision checks. These are previously recorded items,
   not newly observed failures in this run.
3. **Shorter mobile report:** the 390-pixel Light capture is over 11,000 pixels tall.
   Keep a brief overview and first action visible, provide section navigation, and
   make repeated device details expandable. Preserve the cautions and technical
   evidence; reduce repetition rather than hiding uncertainty.
4. **More informative Deep progress:** retain elapsed time, but also distinguish
   a responsive backend, a running scanner and its last progress event. If Nmap
   status output is used, capture it separately from XML and do not imply a
   precise completion estimate for service detection or AI preparation.
5. **Help identify unnamed devices without inventing names:** optionally label
   the verified default-gateway address as "Current network gateway", with its
   source, and make nickname assignment more prominent. Do not turn the gateway
   role or a vendor hint into a verified device identity.

These UX ideas are recommendations, not changes implemented in this pass. The
existing glossary, nickname controls and elapsed-time display already exist;
the suggestions refine how prominently and compactly they are presented.
For completed reports with only a limitation note, also consider the heading
"Scan notes" instead of "Scan notes and unfinished checks".
