# Review remediation and verification plan — 3 October 2026

Scope: preserve existing evidence and uncommitted work; keep FastAPI, one backend,
five admitted jobs and local JSON. Pi-hole remains deferred. No automatic broadening
of network scope, speculative CVEs, invented device names or destructive retention.

## Implementation sequence and acceptance criteria

1. **Scheduling:** separate queued time from active execution, bound queue waits,
   share scanner capacity with discovery, retain responsive cancellation. Test
   five jobs, occupied capacity, queue expiry, cancellation and analysis contention.
2. **Network continuity:** capture authorised network context; recheck before host
   work/retries/enrichment and interrupt on change. Detect long suspend gaps without
   claiming a device failed. Test with injected network changes; never switch scope
   automatically. Keep saved partial evidence accessible.
3. **CVE identity:** bounded authoritative CPE dictionary resolution, explicit
   provenance, conservative ambiguity rejection and separate unresolved status.
   Test deprecated/current identifiers, ambiguity, outage, quotas and privacy.
4. **AI presentation:** prefer validated model fields, retain reviewed fallbacks,
   show truthful attribution and preserve severity/evidence. Test ready, mixed,
   stale, failed and unavailable model results, including zero-finding reports.
5. **CVE access:** eligible services expose references even without a rule finding.
   Test HTTPS-only reports, repeated lookups, saved results and mobile layout.
6. **Optional mDNS:** safe degraded startup when only enrichment is unavailable;
   preserve independent target authorisation and wrong-network rejection. Test
   missing package/interface and ensure skipped naming is disclosed.
7. **Windows scope:** replace translated text dependencies with structured adapter
   data; test locale-independent, disconnected, VPN and ambiguous-adapter cases.
8. **Annotation concurrency:** return/apply complete snapshots after CVE changes;
   stale titles must conflict rather than overwrite another tab. Add regression.
9. **Failure diagnostics:** bounded per-attempt cause/duration/exit information;
   retain attempt evidence, selectively retry transient failures, explain Nmap
   driver/permission failures without exposing raw diagnostics in the main report.
10. **Naming:** fair bounded enrichment for already-discovered devices; disclose
    host/service/time limits. Test more than eight devices without widening scope.
11. **Usability:** action-first coverage and next steps, grouped repetitive content,
    collapsed technical detail and explicit Light/Deep limits. Test mobile widths,
    keyboard navigation, empty/partial/failed reports and refresh recovery.
12. **Storage maintenance:** inspect existing export/recovery/retention facilities,
    fill usability gaps and expose usage. Verify round-trip isolated exports and
    restoration; never automatically delete saved home reports.
13. **Organisation:** extract focused scheduling/network helpers and reusable UI
    logic where useful; document current architecture separately from dated logs.
    Remove nothing without proving it unused and preserving recoverability.
14. **Evaluation:** prepare reproducible reader, physical-device accessibility and
    Ubuntu known-truth lab protocols. Actual human participation and unavailable
    hardware remain explicitly pending, not simulated passes.

## Verification gates

- Focused regressions for each change, then full offline Python/JavaScript suites,
  lint/format, installed-wheel and Chromium/Firefox/WebKit tests where available.
- Local Ollama test using synthetic identifier-free facts; inspect actual accepted
  wording and fallback attribution, not just successful HTTP responses.
- Read-only home-network preflight. Run Light only on the currently authorised home
  scope, then Deep only on the freshly identified Sony. Stop if scope/identity is
  ambiguous or a non-home network is detected. Never change router/DNS settings.
- Save new reports normally, preserve old reports, replay retained XML against
  stored facts, inspect names/coverage/findings/CVE/AI, refresh/history/Run again,
  and mobile rendering. Record exact IDs, outcomes and remaining limitations.

## Status

Implemented: 1–8; per-attempt diagnostics and selective retry in 9; known-host naming
and budget disclosure in 10; collapsed technical details, service CVE access and
explicit coverage in 11; offline checksummed backup/restore plus usage and existing
non-destructive retention preview in 12; focused helper modules/current architecture
reference in 13. No unused source was deleted. Accepted AI fields take precedence;
original evidence is never replaced by model output.

Final local verification: 394 Python tests and 50 JavaScript tests passed, including all
three browser engines, lint/format and module syntax checks. Fresh installed wheel
passed six pages, ten assets, demo workflow and dependency consistency. Public nginx
identifier resolution returned 15 candidate records with recorded provenance.

The first live Light run exposed a new integration defect: per-attempt raw XML names
were not allowed by storage's older filename policy. It saved a failed report and
AI explanation, without claiming successful coverage. The whitelist is corrected;
45 focused supervisor/storage tests passed, including a new raw-enabled end-to-end
persistence assertion. The subsequent Light run checked 11 of 13 devices, honestly
recording two unreachable devices; Sony Deep completed on its first attempt with
15 open services and nine review items. Both evidence replays and mobile checks
passed. A final report-loading Run again race was fixed and navigation retested.
The failed report and its diagnostics are retained. See live-check-20261003.md for
exact results and the external home-fingerprint CVE lookup approval boundary.

Remaining external evaluation: real participants, physical-phone/assistive-technology
sessions and the authorised Ubuntu lab in evaluation-remediation-20261003.md.
Scanner version/adapter readiness does not prove every platform's raw-packet
permissions; comprehensive capability preflight across Linux/Npcap variants remains
a lab follow-up. No app elevation is recommended. Retention deliberately does not
delete reports. Backups require stopping the app.
