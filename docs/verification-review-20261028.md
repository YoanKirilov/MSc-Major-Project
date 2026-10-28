# Live scans and verification review - 28 October 2026

Status: in progress. Final outcomes will replace this status after the checks finish.

## Scope and method

Repeat the authorised Light scan of the home range and Deep scan of this Windows
computer, using a new isolated JSON store. Verify running-refresh recovery,
analysis before report opening, coverage, saved scanner evidence, AI wording,
report/inventory/export behaviour and responsive layouts. Then run offline,
Chromium/Firefox, package and security checks and review the scan architecture.
Preserve normal evidence and existing changes. WebKit navigation remains explicitly
deferred; no WebKit or hosted-CI pass is claimed.

Private artifacts: `.test-artifacts/recheck-live-20261028/`.

## Preflight

- Fresh strict adapter checks confirmed the previously authorised home range and
  this computer's address. The first sandboxed query was denied by Windows CIM
  permissions; the same read-only preflight outside the sandbox passed. That
  sandbox limitation is not counted as a failed application scan.
- Normal backend is reachable with contract 3 and build `5ef8b4b9ad40e95f807b`.
  Current source hashes as `ba42108dd714bdff672e`. Comparing all packaged app
  files with the last tested wheel found only line-ending differences in
  `app/templates/dashboard.html`; its contents match after CRLF/LF normalisation.
  Served static assets match. No functional source difference or reason to stop
  the user's backend was established by this comparison.
- Nmap reports 7.991; local Ollama reports `llama3.2:3b` available. Two fresh scan
  submissions were made through the isolated browser flow, with Pi-hole disabled.

## Findings and recommendations

1. **Low - build freshness can give a false restart warning after line-ending
   changes.** `source_build_id` hashes raw source bytes, including CRLF/LF. A
   formatting-only change therefore makes the normal backend appear outdated.
   Consider canonical line endings when hashing textual build inputs, with tests
   proving that actual Python/JavaScript/template changes still invalidate the
   identity. This does not establish a functional runtime defect.

Further findings and verification outcomes are pending.
