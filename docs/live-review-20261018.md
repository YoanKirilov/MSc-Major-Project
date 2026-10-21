# Live scans, architecture and maintenance review - 18 October 2026

Subsequent implementation: [remaining fixes and verification](remaining-fixes-20261018.md).
That follow-up resolves the CVE/header and smaller presentation findings below,
using saved reports without rescanning. This document retains the original review
state and test results, not a claim that those issues remain unfixed.

## Scope and isolation

The detected default-route network and this-PC address matched the user's previously
authorised home scope. One Light discovery scan and one Deep scan of this PC were
submitted through the browser to a separately owned backend. Pi-hole was disabled.
Normal settings, nicknames and reports were not imported into or edited by the test.
Private evidence is under `.test-artifacts/live-review-20261018-b/`; do not publish
its raw XML, network identifiers, session URL, report text or screenshots.

The app source baseline was `b49c71a`. Its
[GitHub run 23](https://github.com/YoanKirilov/MSc-Major-Project/actions/runs/39079432854)
passed all twelve platform/browser jobs and the security job. That hosted result
predates the local helper-only maintenance below; no new push was made here.

## Live results

| Check | Light | Deep, this PC |
| --- | --- | --- |
| Discovered devices | 10 | Not a discovery scan |
| Device checks completed | 8 | 1 |
| Device checks not completed | 2 | 0 |
| Recorded open features | 12 | 13 |
| Deterministic review findings | 8: four low, four informational | 4 informational |
| Automatic explanation processing | Finished | Finished |
| Duration including explanations | 338.6 seconds | 527.2 seconds |

The two Light failures were `HOST_UNREACHABLE` after two attempts each. The evidence
does not establish whether those devices were asleep, disconnected or refusing a
response. These remain incomplete checks, not confirmed vulnerabilities or proof of
an application fault. Do not remove them or label their checks successful.

Deep has no recorded device-check errors. Its self-scan warning is expected: an
answer on this computer does not establish remote or internet exposure. The live
pair refreshed both active pages and reached their reports without resubmission.
The later saved-report verification submitted **zero** additional scans.

## Architecture review

The existing separation is retained: browser/session and target validation,
supervised bounded scanner work, saved factual JSON, deterministic findings,
then validated local explanation processing. Five admitted jobs share two scanner
workers and one analysis slot; separate tabs are not separate unsynchronised stores.
This review does not justify replacing FastAPI or moving the store to a database.

Source review covered scope/interface checks, interruption monitoring, per-host
attempt records and retry limits, parser completion/target validation, bounded
optional enrichment, JSON write/read limits, and explanation validation. A check
of a service on this computer is not proof of what another device or the internet
can reach; the saved Deep report must retain that self-scan limitation.

## Confirmed open application issues

1. **CVE request deadline mismatch - medium.** `cves.mjs` requests 95 seconds, but
   `api.js` clamps it to 60. The NVD stage permits 45 seconds and the optional
   explanation stage 40, before saving the annotation. Consequently a browser can
   report an unconfirmed failure while the server is still finishing/saving the
   lookup. This is confirmed by source inspection, not a new real NVD timeout.
   Fix with a specifically bounded CVE deadline or separate reference retrieval
   and explanation work. Test the actual requested deadline and saved-result
   recovery without automatically repeating a write. Keep ordinary reads bounded.
2. **Security headers are not actually sent - medium hardening.** A read-only
   request to the running normal backend returned HTTP 200 and `Cache-Control:
   no-store`, but no `Content-Security-Policy` or `X-Content-Type-Options` response
   header. `base.html` supplies meta tags instead. `frame-ancestors` is not supported
   in meta delivery, and `nosniff` is an HTTP response-header defence. Deliver the
   policy and `nosniff` as actual headers, remove misleading metadata, and verify
   HTML/static/API/error/print behaviour. This does not establish an exploit or
   negate existing session/origin checks. See the primary documentation for
   [frame-ancestors](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors)
   and [X-Content-Type-Options](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Content-Type-Options).

These were already identified in the 16 October audit and are still open. They were
not silently marked fixed because scanner or browser tests passed. This request
authorised investigation and code organisation, not a new implementation of those
application behaviours.

## Small verification-code cleanup completed

`scripts/live_review.py` now has a shared final-outcome check: recorded page errors,
overflow errors, wrong submission counts, lost refresh context or changed existing
reports prevent a success message. Previously some recorded failures did not affect
the exit outcome. Artifacts are saved before the outcome check so failures remain
inspectable. Eighteen offline regression cases cover these checks and saved-only
reopening safeguards.

The helper also checks its Playwright dependency before reading normal settings,
creating test data or launching its backend, and directs users to `.venv-quality`.
The initial invocation with the app's runtime `.venv` stopped before submitting any
scan because Playwright is intentionally not a runtime dependency; its owned backend
was stopped. The subsequent browser-equipped invocation submitted the scan pair.

The first pair completed both scans and report/export checks, then stopped at an
outdated inventory-button text selector (`Open recorded reports`). The real UI now
uses `Saved check details and reports`; this was a helper failure, not a missing
report or scanner error. The helper now uses the stable history/summary component
and a CSP-compatible focused-heading assertion, retaining the exact device-key
check. Its original failure record has not been deleted or rewritten as a pass.

`--verify-saved` now reopens the finished pair without submitting scans, redoing
discovery, retrying hosts or regenerating explanations. It validates source/profile
IDs and rejects unfinished jobs before backend startup, so reopening cannot trigger
recovery of active work. New verification output goes in a fresh child directory;
the original raw evidence and failures are retained. Live refresh/automatic-navigation
checks are explicitly **not applicable**, not claimed as new passes, in that mode.
Scan-flow diagnostics are now persisted before later UI checks can fail.

To repeat just the saved-page verification on this evidence, without another scan:

```powershell
.\.venv-quality\Scripts\python.exe -B scripts/live_review.py --verify-saved --artifacts .test-artifacts/live-review-20261018-b
```

Live mode still requires a new artifact folder plus explicit `--authorised`,
`--scope` and `--host` flags, and checks the current network before submitting work.

All 29 JavaScript/CSS assets have a source reference. Ruff found no unused imports
or formatting issues. This is not proof every branch is used, so no application
files, old research evidence, environments or user data were deleted. No broad
controller rewrite was needed for this verification task.

## Verification

- Final offline gate `.test-artifacts/checks-cef9df8808/`: **891 Python passed**,
  five Windows link-privilege skips, 147 opt-in/browser cases deselected; **252
  JavaScript passed**, all 27 module syntax checks, lint and 184-file format check
  passed. The earlier pre-cleanup gate passed 873 Python tests.
- Focused browser run `.test-artifacts/live-review-browser-20261018/`: **14 passed**,
  one deselected. CVE browser cases use a synthetic database, not NVD traffic.
  Independent Light/Deep tab, refresh and cancellation cases cover Chromium and
  Firefox across the selected viewports.
- Installed wheel `.test-artifacts/package-e0a06c75a1/`: dependency checks, seven
  pages, 29 assets, synthetic create/reopen/delete/Undo passed. This build has the
  same application code; the later edits affect the development helper/tests only.
- Focused helper cases `.test-artifacts/live-helper-20261018-c/`: **18 passed**.
  An earlier sandboxed invocation could not access pytest's temporary folder;
  the approved rerun passed in a fresh folder. No network checks run in these tests.
- Read-only raw XML replay matched all **120 Light + 20 Deep service records** and
  **twelve deterministic findings**; no completed-host raw evidence was missing.
  Two saved Light certificate-date interpretations also matched the original facts.
- All **twelve ready explanation records**, including both overviews, passed
  reviewed-choice revalidation. No rejected fields were recorded. The other two
  records are explicit `not_simpler` fallbacks, not accepted AI rewrites. The audited
  AI input contained no recorded device identifiers, network range or raw XML.
- Saved-page verification
  `.test-artifacts/live-review-20261018-b/verification-9e6b2d54d0/` passed both reports
  at **320, 390, 768 and 1440 pixels**, with no page errors or horizontal page
  overflow. Checked feature sections, two private export previews, inventory
  filters/reset and exact device return-focus. The periodic-check route returns
  404. Full-page, viewport and one-device screenshots were saved; viewport/card
  images and the rendered report text were inspected for readability.
- Saved-only checks submitted zero scans and left all saved test evidence
  byte-for-byte unchanged. Both owned test backends stopped; the normal backend
  was not stopped or reconfigured. Comparing all **853 normal report/evidence
  files** with the pre-live hashes showed no changed, added or missing files.

The original helper invocation is not represented as a clean end-to-end pass: it
failed on the stale selector after both live scans finished. The fixed helper's
saved-only checks and offline regressions passed separately. Normal browser/API
assets matched current source, but this does not independently fingerprint every
already-loaded Python module in the normal backend.

## Readability and next improvements

Light's saved overview accurately distinguishes eight checked devices from two
unfinished checks. It describes review findings as observations, not proof of a
break-in. Two finding records retained reviewed fixed wording with `not_simpler`
because the model did not improve it; six finding records and the overview have
accepted model wording. Finishing analysis does not mean every sentence was newly
generated or that every device was checked successfully.

All five Deep explanation records were accepted. Deep shows four review-only
observations with no assigned risk, not four confirmed vulnerabilities. The mobile
card keeps its address, source, check status and observed-feature/review counts
visible; buttons remain contained. The Light heading explicitly names the two
unchecked devices instead of implying a complete check of the whole household.

For the next UI/content iteration, replace user-facing jargon such as "open
services" in the overview with explained "features that answered" wording; keep
protocol/port terms in technical detail. Distinguish informational observations from
settings that actually need attention without changing their saved priority. Give
device-specific, safe next-step examples where supported by evidence, rather than
asking an inexperienced user simply to decide whether an unfamiliar connection is
expected. These are proposed improvements, not changes made in this review.

Two smaller accessibility/content cleanups remain: the report has a legacy
`sr-only` `finding-metric` span that repeats the already labelled review total as
an unlabelled number, and the self-device card repeats its role in two adjacent
lines. Remove the redundant metric/updater while preserving the labelled `dl`,
and combine the role wording without dropping the self-check limitation. Actual
screen-reader speech was not tested, so no specific announcement is asserted.

Actual novice comprehension, screen-reader/voice/switch use, physical-phone Safari
and true browser zoom still need participant/device evaluation. Automated reflow
and focus checks do not establish accessibility conformance. Public NVD compatibility
and Pi-hole were not exercised in this session.
