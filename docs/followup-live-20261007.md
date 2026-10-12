# Nickname and plain-language follow-up — 7 October 2026

## Implemented and verified

Executed [the ordered plan](nickname-guidance-plan-20261007.md) following
[the earlier live review](postfix-live-review-20261007.md).

- Extracted nickname snapshot handling into `static/js/nicknames.mjs`. Older polls
  and full-report reads cannot replace a newer adopted revision. A successful edit
  acknowledgement reserves the new revision before its full snapshot arrives.
  Invalid replies cannot partially update names or notices. Conflicts reload the
  latest names without automatically resubmitting a write; uncertain saves and
  unavailable storage have distinct messages. Filters, expanded device sections,
  checklist disclosures and keyboard focus survive nickname updates.
- Naming guidance and its actual button now share **Try identifying this address
  again**. The glossary consistently explains **Unnamed device**.
- Confident, probed Windows/VMware feature names get conditional **About this
  feature** help and safe places to inspect settings. Port guesses do not qualify;
  no new finding, severity change or verified operating-system identity is implied.
  Windows instructions draw on Microsoft's
  [firewall documentation](https://support.microsoft.com/en-us/windows/security/windows-security/firewall-and-network-protection-in-the-windows-security-app)
  and [file-sharing documentation](https://support.microsoft.com/en-us/windows/experience/connectivity-networking/file-sharing-over-a-network-in-windows).
  The guidance does not instruct readers to enable sharing, disable protection or
  stop core services. VMware help is an explicitly unverified service-name clue.
- Light explains whether its recorded scan computer was included, left unchecked,
  or not discovered. This uses the saved context and target ledger, not an invented
  device result. No coverage counts change and no extra scan starts automatically.
- Duplicate next-step checklists start collapsed on narrow screens, with their
  controls still available on expansion. The primary review-item checklist remains
  visible. The first-action caution is also expandable; evidence and limitations
  remain available.

During development, the broader AI-retry browser regression exposed a new boundary
mistake: compact progress responses were receiving full-report nickname projection.
This could stop report polling after an AI retry. Projection now requires an actual
device array, and nickname rerendering requires a finished full report. The focused
AI-retry test and a new compact-progress regression passed after correction. An
earlier WebKit test also assumed pointer clicks focus native buttons; the conflict
test now explicitly exercises keyboard focus across all three engines.

## Final automated verification

| Check | Final outcome | Private artifacts |
| --- | --- | --- |
| Python, including Chromium/Firefox/WebKit browser regressions | 518 passed; one separately opt-in real-provider test deselected | `checks-0c4fc77de8/` |
| JavaScript regression | 73 passed | `checks-0c4fc77de8/` |
| Lint, formatting, module syntax | Passed; 132 Python files formatted, 11 JS modules checked | `checks-0c4fc77de8/` |
| Focused delayed nickname/conflict browser test | All three engines passed | `followup-nickname-browser-final-20261007/` |
| Focused AI-retry regression after correction | Passed, as did all five nickname unit tests | `followup-ai-retry-browser-final-20261007/` |
| Fresh installed wheel after the final source fix | Six pages, 12 assets, demo read/create/reopen and dependency consistency passed | `package-c65bd0d9ff/` |
| Security checks | No known pinned-dependency advisories or potential secrets; 15 low static findings, zero medium/high | `security-5665a570da/` |

Artifacts are beneath ignored `.test-artifacts/`, not committed public evidence.
The security gate preceded the final JS compact-progress guard; there were no Python
production or dependency changes afterward. The final complete regression and
installed wheel include that guard. These checks are not a security certification.

## Actual authorised live results

Fresh preflight confirmed the home Wi-Fi and authorised scope agreed. Nmap **7.991**,
local Ollama **llama3.2:3b**, storage and session readiness passed. Exactly one Light
and one Deep of the Windows computer running NetGuard were submitted through the
UI to an owned loopback instance with fresh isolated JSON storage. No Pi-hole,
NVD-provider lookup, exploitation, packet capture or unrelated device Deep ran.

| Observation | Light | Windows-computer Deep |
| --- | --- | --- |
| Scan ID | `6c2b06aa-0747-409a-803f-6a090b710fbf` | `076bcd66-11f5-4c44-b369-a91ce2dbd6cc` |
| Approximate observed wall time | 307.9 s | 541.1 s |
| Device checks finished | 9 of 10 discovered | 1 of 1 selected |
| Open services / review items | 12 / 8 | 14 / 4 |
| Priority breakdown | 4 low, 4 informational | 4 informational |
| Final saved outcome | Partial: one unreachable host | Partial: adapter query timed out before enrichment |
| XML service records / deterministic findings replayed | 135 / 8 | 21 / 4 |
| AI records accepted and revalidated, including overview | 8 | 5 |
| Reviewed wording retained instead of an AI record | 1 item: `not_simpler` | None |
| Rejected AI fields | 0 | 0 |
| Recorded mDNS advertisements / currently named checked devices | 3 / 2, both mDNS names | 0 / 1 reverse-DNS name |

Light's unreachable host had two short Nmap attempts; the cause of its absence was
not established. The visible headline says **Scan finished; 1 device could not be
checked**, with the reason and a retry option. The scan computer was not discovered
by Light; the new coverage note correctly explains that its device checks were not
included. Two earlier completed device observations remain separate from current
results; one carries an earlier name. They do not inflate coverage or prove identity.

Deep's Nmap host process completed successfully in 486.636 seconds and its saved
services replay exactly. Before optional announcements/name/detail enrichment, the
strict Windows connection query exceeded its eight-second timeout. The guard stopped
further probing and recorded `NETWORK_INTERRUPTED` / `adapter_query_timeout`.
The report preserves completed observations, its self-check warning and the
unfinished-stage limitation; optional device details were not collected. It would
be incorrect to describe this Deep run as wholly successful or all checks completed.
Automatic Ollama still prepared all five report/item records after interruption.

All ready explanations were revalidated against their reviewed alternatives;
all 12 deterministic findings reproduced from saved XML. Rebuilt model input
contained no observed IPs, MACs, hostnames or raw XML. The one Light fallback is
the simpler-wording guard working as designed, not a provider outage or hidden
finding. No severity or evidence was changed by the new display help.

## Browser, architecture and preservation review

- Both active jobs survived page refresh without another submission. Deep restored
  its immutable target and disabled setup while running.
- Finished reports passed history search/reopen and Run again navigation. The actual
  identification label, new self-coverage note and Windows help rendered correctly.
- Live Chromium reports fit widths **320, 390, 768 and 1440 px** without horizontal
  page overflow. Mobile checklist expansion exposed the controls. No browser page
  errors occurred; exactly two live scan submissions were recorded.
- Viewed the captured mobile flow and read both report texts from a beginner's
  perspective: clear first action, distinct review-versus-risk counts, current versus
  older names, incomplete checks, safe configuration inspection and self-reachability
  limits remain visible. This is an author review, not a participant study.
- All **66 Python application modules** remain statically reachable. Five pages and
  the unauthenticated API boundary returned their expected statuses; all **12 static
  assets** on the owned test instance matched disk and were served without caching.
  No application file was proven redundant or deleted. Nickname logic was extracted
  for a concrete consistency boundary, not a wholesale renderer rewrite.
- Original normal reports and copied baseline reports passed hash preservation.
  The owned test backend was stopped and port 8766 no longer listened. The user's
  normal port 8765 was observed listening afterward and was not stopped or modified
  by this harness. Its authenticated runtime was not separately certified.

Live evidence, timelines, replay, screenshots and integrity/cleanup records:
`.test-artifacts/followup-live-20261007/`. New live reports are in its isolated data
folder, **not** automatically added to normal saved-report history.

## Remaining issues and next executable work

1. **Investigate Windows adapter-query reliability without weakening scope safety.**
   Three bounded read-only checks after the interruption succeeded in 3.985, 3.840
   and 3.917 seconds and still contained the home address. This establishes recovery,
   not the cause of the earlier timeout. Preserve the diagnostic reason and failed
   report. Measure query/queue latency during paired jobs and status polling; compare
   a lighter structured adapter source with the current connection/profile/address/
   gateway fields. Add equivalence, ambiguity, route-change and failure-closed tests
   before replacing the source. Do not silently use stale snapshots, ignore the guard,
   increase scan scope or mark skipped enrichment complete. Repeat authorised live
   checks after any verified implementation. No speculative guard change was made.
2. **Complete human/device evaluation.** Run the prepared nontechnical-reader task,
   physical-phone/keyboard/screen-reader checks and authorised Ubuntu lab evaluation.
   Automated mobile widths are not all physical devices or assistive technologies.
   Compare time to identify the device, understand a review item and locate a safe
   next action, rather than just asking whether the page looks clear.
3. **Continue evidence-led simplification.** Test whether readers can find the new
   Windows help and distinguish expandable duplicate checklists from scan coverage.
   Only then change repetition or action grouping; retain original evidence and
   precautions. Consider further renderer extraction when another independently
   testable state boundary is identified.

The intermittent Windows socket-shutdown reset remains a separate prior runtime
follow-up; it did not recur in this test log. Pi-hole deployment and live external
CVE-provider evaluation stay deferred. No claim that every possible defect is fixed
is made. Use a hard browser refresh to load the updated frontend.
