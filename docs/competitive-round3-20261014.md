# Third comparison and verification — 14 October 2026

Continue from [round two](competitive-round2-20261014.md); do not repeat already
implemented inventory, comparison, export, filtering or SMB features as new work.
Keep JSON, evidence, recovery and the small Light scan contract.

## Evidence and selected gaps

- [Fing events](https://help.fing.com/hc/en-us/articles/26812095708828-Recent-Network-Events)
  provides sequential network events. NetGuard has bounded saved observations and
  optional periodic events, not continuous presence. Do not fabricate online/offline
  timelines or join times. Improve navigation through its actual saved records.
- [Angry IP Scanner](https://angryip.org/documentation/) documents modular name and
  service fetchers. NetGuard already has bounded DNS/mDNS/NetBIOS discovery. Review
  the existing fetchers for reliable evidence rather than adding redundant traffic.
- [Nmap nbstat](https://nmap.org/nsedoc/scripts/nbstat.html) documents computer names
  and potentially logged-in usernames. Current NetGuard code correctly avoids saving
  raw replies/usernames, but can silently choose the last of several host/script/name
  matches. Extract exactly one bounded endpoint-bound computer name or explain why
  the result was unavailable; never infer identity from a contradictory reply.
- [Nmap XML](https://nmap.org/book/output-formats-xml-output.html) distinguishes port
  guesses from probed service identification. Existing NetGuard feature labels
  already qualify guesses; retain that contract and its tests, not a new risk score.
- [NN/g expectations](https://www.nngroup.com/articles/efficiency-vs-expectations/)
  supports familiar controls and explicit feedback rather than hidden save behaviour.
  Interpretation here: preserve the applied inventory view when returning from a
  report, without claiming that household-label drafts were saved.
- [W3C regions](https://www.w3.org/WAI/tutorials/page-structure/regions/) supports
  meaningful navigation/regions. Keep native links, accessible result headings and
  deliberate focus rather than introducing an overlay or replacing browser Back.

## Implementation order

1. Add bounded, expiring per-tab inventory reading context: only applied search,
   view, page, scroll and an optional opaque card reference. Do not persist drafts,
   labels, scan permissions, credentials or raw scan data. Ignore malformed/expired/
   blocked storage; preserve reset and page correction. Never scroll over user input.
2. Keep a useful report link and a reliable return path; restore the applied list
   and prior place on reload/return. Verify keyboard focus, filtering and mobile
   reflow. Retain the browser's native navigation semantics.
3. Extract a pure bounded NetBIOS interpreter. Reject wrong/multiple hosts,
   duplicate/malformed/error/conflicting scripts and unbounded XML/output. Keep only
   one computer name, not users, groups or raw script output. Report suitable bounded
   failure reasons. No added ports/scripts or retry count; both profiles benefit.
4. Add focused Python/JS/browser regressions, then the full offline gate, installed
   package and Chromium/Firefox checks. Preserve first failures and affected retests.
5. Reconfirm the same authorised home route. Only then run fresh isolated Light and
   this-PC Deep scans, review actual plain-language reports and replay evidence/AI.
   Keep Pi-hole, external CVE lookups and periodic execution off. Verify normal data
   integrity and owned-process cleanup; record limits and remaining evaluation.

## Results

The selected changes are implemented. Prior-round counts are not current evidence.
Physical-device, screen-reader and novice-reader evaluation remains unverified.

The initial focused test command had two fixture setup errors with oversized
parameter identifiers under Windows; the identifiers were bounded. The corrected
focused run passed 87 cases. Five process-failure cases were then added and included
in the full gate. Initial full-gate lint stopped on an overlong verification-helper
line; it was fixed before the successful rerun, not ignored.

The full offline gate `.test-artifacts/checks-f1b60234db/` passed 871 Python tests,
six actual Windows link-privilege skips, 113 browser/provider/study deselections,
242 JavaScript tests, Ruff, 179-file formatting and 28 shipped syntax checks.
`.test-artifacts/package-feb992c125/` passed seven installed pages, thirty assets,
synthetic API/report removal/recovery and clean dependency checks using the local
wheelhouse. All 117 installed application files matched source byte-for-byte.

The first focused inventory browser matrix
`.test-artifacts/competitive-round3-inventory-browser-20261014-a/results.xml`
passed all twelve Chromium/Firefox cases. The return case was subsequently extended
to exercise native browser Back as well as the navigation link. The focused retest
`.test-artifacts/competitive-round3-back-retest-20261014-a/results.xml` passed both
Chromium/Firefox cases, with ten unrelated cases deselected. The wider matrix is
recorded below. No browser case sent scan traffic.

Read-only preflight confirmed the same authorised home range `192.168.0.0/24`, this
PC `192.168.0.216` and interface `eth6`. No probes ran during the offline gates.

The wider `.test-artifacts/competitive-round3-browsers-20261014-a/results.xml`
matrix passed all 64 selected Chromium/Firefox cases, zero failures/errors/skips
(453.408 seconds). The extended native Back cases passed separately as above.
Final lint, 179-file formatting and `git diff --check` passed; line-ending
conversion warnings are not code failures. No application files changed after the
verified package build. The fresh live pair uses the new ignored isolated folder
`.test-artifacts/live-review-20261014-g/`. Completion, raw replay/AI validation,
normal-report integrity and cleanup are recorded below.

The baseline pair finished before the requested interface simplification began.
Light completed in 268.7 seconds: ten devices, twelve open features, eight review
items and no scan errors. Deep completed in 516.8 seconds: one device, fourteen
open features, four review items and no scan errors. Replay matched all 171 saved
service records and twelve findings; two Light certificates revalidated and no
raw evidence was missing. Identifier-free AI inputs passed validation, but Ollama
was unreachable: all fourteen explanation records correctly used the explicit
provider-unavailable fallback. No model-written wording was revalidated this run.
Both concurrent jobs survived dashboard refresh, reports opened automatically,
eight viewport captures were produced and the browser reported no page errors.
Inventory return context and private exports passed; existing normal reports
were unchanged and the isolated helper stopped its owned backend. Artifacts:
`.test-artifacts/live-review-20261014-g/`. These results do not verify the later
UI changes or periodic-feature removal, tracked separately in
[UI simplification](ui-simplification-20261014.md).
