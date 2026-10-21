# Remaining application fixes - 18 October 2026

Follow-up to the [live review](live-review-20261018.md), implementing its confirmed
CVE deadline, response-header and smaller readability/accessibility findings.
The earlier review remains a record of the application tested at that time.

## Execution plan and implementation

1. **Align CVE deadlines and provide non-destructive recovery.** `api.js` now
   permits a maximum 110-second timeout only for the explicit service-CVE POST.
   This accommodates the bounded 45-second NVD and 40-second local-wording stages,
   storage and response delivery. Ordinary calls retain their 20-second default
   and 60-second maximum; the CVE caller uses the shared deadline constant.
   No request is automatically repeated. A lost, timed-out or server-error reply
   is unconfirmed, not proof that saving failed. The panel disables another lookup
   and offers **Reload saved CVE references**, which reads annotations with GET.
   It preserves prior references, rejects stale snapshots, displays recorded dates
   and restores keyboard focus appropriately. Empty or failed recovery reads keep
   the uncertainty visible rather than claiming success. CVE eligibility, matching,
   qualified related-product references and locally constructed NVD links are unchanged.
2. **Deliver security controls as HTTP response headers.** The shared pure-ASGI
   `security/headers.py` middleware sets `no-store`, a self-only Content Security
   Policy, `nosniff`, `DENY` framing and `no-referrer`. Normal HTML, JSON, static
   assets, authentication failures, 404/405 and conditional/range replies receive
   them without losing their MIME or other response headers. Unexpected 500 replies
   have the same protection and generic JSON, while server exceptions still log
   and propagate normally. Unsupported framing/MIME meta tags were removed.
   See [MDN on frame-ancestors](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors)
   and [nosniff](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Content-Type-Options).
3. **Keep startup working under the enforced policy.** Dashboard/report static-preview
   redirection and module-error recovery now use a shared external `startup.js`.
   Relative bootstrap URLs work both from Live Server's template path and backend
   routes. A failed initial module can offer Reload page without starting a scan.
   There are no inline handlers, `unsafe-inline`, `unsafe-eval` or remote script
   exceptions. FastAPI's unused CDN/inline-based Swagger and ReDoc pages are
   explicitly disabled instead of serving broken developer UIs; `/openapi.json`
   remains available. Home-user pages and authenticated API contracts are retained.
4. **Clarify report reading without changing evidence.** The report has one labelled
   review count instead of an extra unlabelled hidden duplicate. The self-device
   card states its scan-source role once. Reviewed overview labels display
   "features that answered", with a short everyday definition, instead of
   unexplained "open services". Counts, incomplete checks and stored model text
   remain unchanged. Review-only observations are distinguished from confirmed
   problems without weakening low/medium/high findings. Where reliable saved
   service evidence supports it, the first informational next step reuses existing
   conditional Windows/feature help and safety precautions instead of generic advice.
5. **Verify the actual policy and saved reports.** Browser assertions now wait
   without page-world `Function` compilation; text-spacing overrides use CSSOM
   or same-origin stylesheets rather than blocked inline styles. No application
   policy is bypassed. The CVE library test targets its lookup control explicitly,
   distinguishing it from the new recovery control. The saved-review helper waits
   for the applied inventory filter and completed loading before opening a card,
   so it cannot click a disappearing row from the previous view.

## Verification record

All new test data and build products are below ignored `.test-artifacts/` folders.
There were **no new network scans, host retries, explanation regeneration or public
NVD requests** in this fixes pass.

- Final offline gate: `.test-artifacts/checks-0992a44b30/`: **914 Python passed**,
  five Windows link-privilege skips and 150 opt-in cases deselected; **261 JavaScript
  passed**, all 28 JavaScript syntax checks, Ruff and 188-file formatting passed.
  `scripts/check.py` exited successfully. Before the API-doc compatibility adjustment,
  `.test-artifacts/checks-7c04387d40/` also passed with 910 Python and 261 JavaScript.
- The broad Chromium/Firefox gate `.test-artifacts/checks-fd8c53392b/` originally
  returned **1,195 passed, five failed, five skipped, two deselected**. Four failures
  were test-only inline styles correctly blocked by the new CSP; the fifth was an
  ambiguous test locator after adding the CVE recovery button. None was ignored.
  The affected files passed a **nine-case rerun** in
  `.test-artifacts/remaining-browser-rerun-20261018/`. This is combined evidence,
  not a claim that the original broad command exited successfully or was rerun
  entirely after the corrections.
- Focused header/print, CVE and report-insight browser checks passed **14 cases**
  against the final server changes in `.test-artifacts/remaining-browser-final-20261018/`.
  CVE cases include a real synthetic backend save followed by a deliberately lost
  browser response, then GET-only recovery with exactly one lookup submission.
- The earlier focused run `.test-artifacts/remaining-focused-20261018/` passed
  **31 cases**, including header contracts and bounded browser-condition helpers.
- Saved home-report verification
  `.test-artifacts/live-review-20261018-b/verification-08c89f3c3d/` passed both
  reports at **320, 390, 768 and 1440 pixels**, two private export previews,
  inventory filters/reset and exact device return-focus. It recorded **zero scan
  submissions**, no page errors or page overflow, and byte-for-byte unchanged
  saved test evidence and normal existing reports. The owned backend stopped;
  the normal backend was not stopped or reconfigured. Desktop overview and mobile
  device-card screenshots and rendered text were inspected. This reopens the
  previous live pair; it does not repeat live refresh/analysis-navigation testing.
- The first saved-only follow-up, `verification-a8cdaa88a4/`, failed on the helper's
  old-view inventory timing race. It recorded no page errors and no submissions;
  its backend stopped. The fixed helper's successful run is separate evidence.
- The final installed-wheel check uses cached wheels only:
  `.test-artifacts/package-0abeb73071/`. It passed seven page routes, 30 assets,
  dependency integrity and synthetic report create/reopen/delete/Undo. Earlier
  `.test-artifacts/package-5eb7097766/` also passed, before the last small copy/API-doc
  compatibility adjustments. No runtime environment or real report was replaced.

Repeat the completed offline, focused-browser and package checks without scanning:

```powershell
.\.venv-quality\Scripts\python.exe -B scripts/check.py
$env:RUN_BROWSER_TESTS = "1"
$env:RESPONSIVE_BROWSERS = "chromium,firefox"
$env:UI_UX_BROWSERS = "chromium,firefox"
# Use a new, short --basetemp and cache_dir each time.
.\.venv-quality\Scripts\python.exe -B -m pytest tests/browser_test_inclusive_accessibility.py tests/browser_test_setup_tools.py tests/browser_test_library.py tests/browser_test_response_headers.py tests/browser_test_cves.py tests/browser_test_report_insights.py --basetemp .test-artifacts/remaining-browser-next --override-ini cache_dir=.test-artifacts/remaining-browser-next-cache
.\.venv-quality\Scripts\python.exe -B scripts/check_package.py --offline --wheelhouse .test-artifacts/home-review-20261008-wheelhouse
```

The wheelhouse is local ignored build data, not a file supplied by a Git clone.
On another installation, provision the pinned dependencies first or use the normal
package-check command with explicit index access. Browser binaries must already
be installed. These commands do not opt in to live scans or real-provider tests.

## Handoff and remaining limits

Restart **NetGuard: Start backend** once, after current scans finish, and hard-reload
the browser to load the new server headers and startup assets. An already running
Python process does not necessarily reload them. Do not stop someone else's backend
or copy test session tokens into normal settings.

No source files or user reports were deleted; no commit, push or repository setting
change was made. GitHub run 23 is the green **baseline**, not evidence for these
unpublished changes. Local Windows WebKit remains blocked by OS code-integrity
protection; no OS protection or browser-engine check was disabled to obtain a pass.

Actual screen-reader/voice/switch use, physical Safari/phone checks and novice-reader
evaluation remain outstanding. Automated checks do not certify accessibility or
comprehension. The two earlier unreachable Light devices remain truthful incomplete
checks. Neither keeping Ollama warm nor a longer CVE deadline guarantees an external
dependency will always return an acceptable result. Storage, scan scope, deterministic
findings, AI validation and severity contracts were not relaxed.
