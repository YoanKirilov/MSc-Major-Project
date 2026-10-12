# Beginner-reading fixes and verification — 12 October 2026

Later same-day work: [new live findings and UI/UX execution](ui-ux-live-followups-20261012.md).
The snapshot and counts below preserve the earlier run.

Implements the [execution addendum](live-ui-repeat-20261009.md) while preserving the
current visual design, local JSON, scan evidence, risk severities, authorisation,
single-backend concurrency and revision-safe edits. Pi-hole remains deferred; no
automatic CVE/provider requests were added.

## Implementation

| Item | Result |
| --- | --- |
| Scan/progress read I/O errors | Retryable HTTP 503 with a two-second Retry-After hint and a same-scan recovery message. Missing/invalid, permission and lock errors remain distinct. |
| Full-address search | A complete valid IPv4 query matches the device address exactly, not a prefix, hostname or address mentioned in old notes. Partial/text searches remain available. |
| Unchecked cards | Explicit not-assessed previews replace misleading empty counts; any genuine partial observations remain separate from unfinished checks. |
| Feature details | One native disclosure per device, beside About this device, groups all answering-feature names, versions and recorded check output. No per-row disclosure or evidence truncation was introduced. |
| Compact reading | Tighter feature rows, shorter consistent headings and secondary technical context preserve item/port association. |
| Paragraph alignment | Longer report explanations are justified by default. Reading preferences offers left alignment; the bounded per-tab state preserves it across reload. Labels, controls, short status/context and technical output remain left-aligned. |
| Beginner help | Conditional Windows/VMware/video-stream/name-lookup explanations are visible beside the finding, not buried in provenance. A guided recognition path, glossary links and first-action HTTP/password/certificate precautions give a safe starting point. |
| AI | Approved ordinary-language alternatives revised; prompt bumped to 4.3.0. Source-bound validation, identifier-free inputs, bounded batches and evidence-preserving fallback remain intact. |
| Windows callback | Investigated, not marked fixed; see limitations below. |

Technical sections use text nodes, not parsed scanner HTML. Open grouped evidence
and keyboard focus survive projections/reload; earlier per-feature reading keys can
open the new grouped disclosure. Rendering, glossary/reading controls and setup
navigation do not submit scans, name lookups or CVE requests.

The left-aligned option is deliberate: full justification can introduce uneven gaps
that some readers find difficult. [W3C visual-presentation guidance](https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html)
describes a mechanism for choosing nonjustified text. This is not a claim of full AAA
conformance. Ordinary language and inline help follow [W3C clear-word guidance](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o3p01-clear-words/).

## Offline verification

- Fifteen focused API cases cover generic I/O, missing/invalid reports, permission
  and lock errors across scan metadata, complete results and progress. No scan was
  submitted and saved JSON was unchanged.
- Nine new three-engine synthetic cases cover grouped evidence, reading preference/
  disclosure reload, prefix/name collision searches, recognition, failed previews,
  adjacent precautions and keyboard-accessible glossary opening.
- Final `scripts/check.py --browser --browser-engines chromium,firefox,webkit`
  passed **712 Python/browser tests and 106 JavaScript tests**, with one real-provider
  case deselected. Ruff lint/format passed for 144 files, with all 15 module syntax
  checks. Artifacts: `.test-artifacts/checks-f415cb7153/`.
- After the live report revealed closed-early connections, two display-only
  clarifications were added: explain unknown purpose without guessing software,
  and keep Windows-only limitations out of streaming/name-lookup help. The final
  source passed a fresh offline gate: **597 Python and 107 JavaScript tests**,
  lint/format and 15 syntax checks in `.test-artifacts/checks-1befb598c8/`. The
  final read-only three-engine live-report pass below used those finished changes.
  The earlier 712-case full gate is not claimed as a rerun after these clarifications.
- Early runs were not counted as passes: Windows sandbox process/temp permissions
  prevented test startup; an old per-feature selector and old VMware-label expectation
  needed updating for the new contract; lint caught import order, and a legacy test
  read the UTF-8 template with Windows' default encoding. The latter now explicitly
  reads source as UTF-8. All assertions were preserved or updated to test the new
  structure; no regression was skipped to obtain the final pass.

## Live verification

The confirmed home range remained `192.168.0.0/24`, with this PC at
`192.168.0.216`. Exactly one Light and one this-PC Deep run were submitted through
an owned backend on 8766, using fresh isolated JSON and unchanged copied comparison
evidence in `.test-artifacts/readability-live-20261012-b71c84/`. The full synthetic
gate completed successfully while the live runs were progressing. Existing normal
reports and both copied historical reports retained their hashes. The new results
are isolated evidence, not entries in normal app history.

| Result | Light home network | Deep this PC |
| --- | --- | --- |
| Scan ID | `a4f695fa-f7ee-4aa6-afa7-e2b90917819c` | `28fec110-4bb6-474f-9c81-920aef08b24c` |
| State / device coverage | Completed; 7/7 discovered checks finished | Completed; 1/1 selected check finished |
| Open features / review items | 10 / 7: three Low, four informational | 14 / 14 informational |
| Scan errors | 0 | 0; expected self-routing warning retained |
| AI records including overview | 8 ready | 14 ready; one unchanged-wording fallback |
| Elapsed including analysis | 312.4 s, about 5 min 12 s | 596.0 s, about 9 min 56 s |

The runtime was Nmap 7.991, Python 3.14.2, local Ollama `llama3.2:3b`, prompt
4.3.0. XML/rule replay matched **126 service records and 21 findings**; all
**22 ready AI records** revalidated with zero rejected fields. One Deep record
retained reviewed guidance because no accepted clearer alternative was produced
(`not_simpler`), not because the model was unavailable. Selected AI payloads contained
no device/coverage identifiers, CIDR or raw XML.

Deep recorded `tcpwrapped` for all 14 answering TCP connections: the connection
closed before software identification. Product/version fields were absent. Those
are informational observations, not 14 vulnerabilities; names such as Windows RPC
or VMware were not guessed from ports. The physical cause of early closure was
not established. Testing the PC from itself does not establish reachability from
another device or the internet. The new visible help and shorter unknown-feature
title explain these limits and warn against disabling protection just to clear a result.

Light observed fewer devices than on 9 October; four earlier completed observations
were not matched and remain uncertain, not marked removed or repaired. It retained
two mDNS announcements, one current reported name and one clearly qualified previous
name; five usable results had no name. Deep retained a reverse-DNS name. Four Light
services were eligible for optional precise-version CVE research and none in Deep
were; no CVE match, provider lookup or Pi-hole request is claimed.

Refresh recovery and automatic report opening after analysis passed for both jobs,
with exactly two scan submissions. The final saved-report viewer passed **16
engine/profile/viewport combinations**: Chromium 320/390/768/1440, Firefox and
WebKit 390/1440. It checked one grouped feature disclosure with all recorded answering
features, disclosure/selection reload, reading-preference reload, exact-IP search,
history reopening, and Light/Deep Run again setup, without scan/edit submissions.
No page errors or horizontal page overflow occurred. All 16 served assets matched
finished source bytes with `no-store`; reopened evidence hashes were unchanged.
Final browser artifacts: `browser-check-7e9c88ec/` within the live folder. The earlier
passing `browser-check-21af43da/` and intermediate check logs are retained separately.

Rendered overviews and the main explanations in all 21 review-item texts were
captured/read; mobile feature/detail screenshots were visually spot-checked. That
review caught and corrected unrelated Windows wording under a streaming explanation.
The final text keeps the context relevant while preserving original guidance and
provenance. No extra network scan was needed for these read-only presentation checks.

Owned scan/viewer backends were stopped; final inspection found the normal app on
8765 and no listener on 8766. No normal-backend restart or authentication was performed.
Isolated scan/viewer logs had no tracebacks, reset callbacks or ERROR entries. Private
bootstrap logs and identifying scan artifacts require sanitisation before publication.

## Remaining limits

The bounded Windows loopback diagnostic passed 11 orderly/10 abrupt disconnects
and 20 concurrent synthetic subprocesses on Python 3.14.2, with no lifecycle
diagnostics. That is not proof the earlier intermittent callback has been fixed.
The [CPython transport source](https://github.com/python/cpython/blob/main/Lib/asyncio/proactor_events.py)
still has the unguarded shutdown path identified by the existing synthetic
reproduction. No private monkey-patch, error suppression or unsupported event-loop
switch was introduced. [Python's Windows platform documentation](https://docs.python.org/3.14/library/asyncio-platforms.html)
explains why switching to SelectorEventLoop would break asyncio subprocess support.

The novice review is editorial, not a study with participants. Real-reader
comprehension, screen-reader/physical-phone/enlarged-text checks, Ubuntu/lab ground
truth and real Pi-hole/CVE-provider behaviour remain separate evaluation work.

An optional later refinement is to group repeated informational connections by
device/purpose while keeping every port, finding and independent task status
reachable. This Deep snapshot illustrates why that could reduce repetitive
reading; it is not permission to merge evidence or silently drop review items.
