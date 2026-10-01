# Library reliability and evaluation plan — 1 October 2026

## Scope and order

Preserve original scan JSON, nicknames, titles and AI evidence. Keep one backend,
local JSON storage and the existing bounded scan profiles. Pi-hole remains deferred.

1. Fix Deep picker refresh: retain a still-valid selection; never silently replace
   a manually edited target; explain when a retained address is no longer listed.
2. Separate unreadable reports from filtered matches and pagination. Preserve their
   files and show an accessible warning independently of the chosen filters.
3. Distinguish an empty archive from a search with no matches.
4. Include last-check/reachability context in recent-device choices; an announcement
   or failed check must not be described as a responding device.
5. Reduce repeated full-report parsing with a bounded, instance-local cache of compact
   search projections. Invalidate on scan, terminal overlay, title or nickname changes;
   never cache unreadable/unstable input. No new persistent index or database.
6. Add regression tests for the above, including cache invalidation, run full Python,
   JavaScript, three-engine responsive checks and installed-package verification.
7. Prepare reader/physical-device evaluation questions without inventing participants
   or results. Review actual saved report wording separately from comprehension claims.
8. After the fixes, run authorised home Light discovery, then Sony Deep. Verify report
   counts against retained evidence, AI/fallback status, refresh recovery, history,
   naming, picker and responsive layouts. Use isolated test storage and compare normal
   data hashes before/after. Never scan an address guessed from old DHCP information.

## Live-test gate

On 1 October the read-only interface check showed ANGLIA.LOCAL, 10.240.108.0/22,
not the authorised home scope 192.168.0.0/24. The user previously denied authority
to scan that network. No live network test may proceed there.

When home: verify the active route/scope and no competing job, inspect the saved
Sony identity plus a current local observation, then use the unchanged application
Light and Deep profiles. If identity is uncertain, ask which device is authorised.
Record partial coverage honestly and keep failures/evidence accessible. Do not
classify 30 September's successful run as a new test of these changes.

## Completion record

Steps 1–5 implemented. Step 6 passed: 338 Python tests, 45 JavaScript tests, lint,
format and syntax, including the Chromium/Firefox/WebKit responsive matrix. A separate
real loopback Ollama test with synthetic facts also passed, as did fresh-wheel
installation, six pages, nine assets, demo create/reopen and dependency consistency.
Full-suite artifacts: `.test-artifacts/checks-9a3285c344/`.
Package artifacts: `.test-artifacts/package-03ce97abac/`.
Ollama artifacts: `.test-artifacts/library-20261001-ollama/`.
Final focused library browser test passed, including populated Deep picker reflow at
320/390 px (`.test-artifacts/library-20261001-picker/`).

An initial sandboxed unit run failed on Windows temp-directory permissions; isolated
execution outside the sandbox passed. The first full run had 337 passes and one new
browser-fixture failure (a missing required target). The fixture was corrected, then
the full rerun passed. No application defect was hidden by skipping the failing test.

All 41 normal reports validated, and their JSON hashes remained unchanged during the
read-only archive check. A single local cold/warm measurement returned identical
results: 256.7 ms / 58.5 ms, 57 / 16 full-report reads. The remaining reads are nickname
identity anchors. The cache held 41 projections / 671,987 serialized bytes. This is
one local observation, not a general performance guarantee or a large-archive benchmark.
Evidence: `.test-artifacts/library-20261001-review/results.json`.

Step 7: extended `evaluation-session.md` with target-selection/history tasks and
physical-device/Ubuntu procedures. No human participants or physical devices tested.
Reviewed the saved 30 September Sony wording: it separates observations from proof
of compromise, explains services and selected coverage, and offers a cautious first
action. Technical labels such as `tcpwrapped` still appear in service details and are
a candidate for a later glossary improvement; comprehension is not proven by this
editorial review or the model-validation test.

Step 8 is pending the authorised home connection. Neither Light nor Deep was run on
1 October. Pi-hole remains deferred; no router, network or normal backend settings
were changed. Do not relabel previous live results as verification of this release.

After active jobs finish, restart the normal backend and reopen its session link with
a hard refresh to load the new Python code and assets (`20261001-library-fixes`).
