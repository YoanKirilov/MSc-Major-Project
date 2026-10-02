# Network recovery execution plan — 1 October 2026

1. Fix IPv6-first Windows gateway parsing. Test actual-format output, absent IPv4
   routes, virtual adapters and multiple active networks; retain bounded private scope.
2. Correct the normal app's obsolete saved range to the currently authorised /24,
   using its revision/lock/backup storage API. Preserve every saved report.
3. Add explicit Automatic and Manual range controls. Show the effective source and
   detected range. Preserve existing settings semantics and server overrides.
4. Bind each dashboard scan request to the range shown when the user confirms Scan.
   Reject a changed range before creating a scan. A detected network is not permission.
5. Improve mDNS scope/interface diagnostics with useful recovery instructions, while
   retaining the requirement for exactly one matching adapter.
6. Expose honest Ollama readiness states and bounded refreshes. A timeout can mean
   starting or unresponsive, not a proven missing model. Keep the factual fallback.
7. Explain Light duration/coverage and technical service terms without changing the
   scan profiles, risk/severity or original evidence.
8. Run isolated focused tests, full regression/browser checks and installed packaging.
   Verify current local detection and interface binding without another port scan.

## Completion and verification

All eight implementation steps are complete. The Windows detector now handles an
IPv6 gateway followed by an IPv4 gateway. The normal app's saved range was corrected
from `192.168.0.0/24` to the already authorised `192.168.1.0/24`, using revision-based
locked storage with a backup (revision 3 to 4). All saved scan JSON hashes stayed
unchanged. Read-only verification detected the current /24 and matched mDNS to
Wi-Fi address `192.168.1.60` with diagnostic reason `ready`.

Automatic and Manual controls preserve existing settings semantics. Automatic
requires confirmation on each dashboard scan and pins new-backend requests to the
displayed scope; a changed scope is rejected before a job is created. Backend scope
overrides remain honoured and visible. mDNS errors now explain the specific recovery
action. Ollama readiness distinguishes an unreachable service, an unresponsive
service, a missing model and other errors; dashboard timeout rechecks are bounded.
Light timing guidance, elapsed progress and plain-language `tcpwrapped` wording are
implemented without changing evidence or coverage.

Verification on 1 October 2026:

- Focused Python checks: 63 passed.
- Final full regression: 353 Python passed, one live-provider test deselected;
  48 JavaScript passed. Lint, formatting (104 Python files), and eight JavaScript
  module syntax checks passed. Artifacts: `.test-artifacts/checks-7bba06e662/`.
- Browser workflow and responsive checks passed in Chromium, Firefox and WebKit,
  including switching and saving Automatic/Manual scope.
- Final wheel/fresh installation passed six pages, nine assets, demo creation and
  reopening, and dependency checks: `.test-artifacts/package-17e4180ae3/`.
- The first full run had 352 passes and one outdated exact-error-text assertion.
  It was updated to check the explanatory message and both ranges; the complete
  suite then passed. One existing Starlette/httpx deprecation warning remains.
- Settings backup/hash verification:
  `.test-artifacts/network-recovery-20261001/settings-update.json`.

No new network scan or real Ollama generation was performed during these fixes.
The normal backend was not restarted or tested end-to-end through its authenticated
session. The preceding live run remains documented separately in
[the live check](live-check-20261001.md).

## Handover

The earlier restart requirement was completed during the follow-up recorded on
2 October: the idle normal backend was restarted, its authenticated page reopened,
and the updated API verified. All 41 existing reports were preserved. A subsequent
normal home Light scan passed admission and completed analysis; one unreachable
device remained honestly recorded as incomplete coverage.

On continuing, the computer was connected to the previously unauthorised
`10.240.108.0/22` network. The home scope was preserved. The dashboard now offers
Check network again on mismatch and sends no scan request from that action.
27 dashboard tests and authenticated Chromium checks passed; see
[the follow-up evidence](testing.md). Reload the browser to get this final UI fix.
The backend already runs the corrected Python code. Reconnect to the authorised
home network before scanning; detection alone does not establish permission.
