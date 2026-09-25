# Implementation brief status

This is the handover for the eleven agreed items. Verification details are in
`testing.md`; external evaluation steps are in `evaluation.md`.

## Architecture audit fixes (25 September 2026)

Completed in dependency order, without scanning the current shared network:

1. **Network selection:** identify the real default-route network, including ranges
   larger than /24. Never silently substitute a VMware adapter. A saved/active network
   mismatch is shown and scan creation is blocked unless an explicitly selected interface
   matches the authorised scope. Invalid configured ranges produce useful errors.
2. **Storage completion:** a revision-bound `terminal.json` can persist final status when
   the primary report is full. Evidence stays unchanged, history/polling can finish, and
   subsequent writes absorb the marker. Report IDs must match their folders.
3. **Packaging:** include demo JSON in the wheel; verify demo read/create/reopen as well
   as pages/assets. Demo writes now use the atomic JSON writer. The unused empty
   `/api/demo-scans` route, debug runner entry point and orphan CSS rule were removed.
4. **Pi-hole and identity:** preserve healthy name sources when another endpoint fails;
   retain discovery MAC/name/vendor details through service checks. Sources are labelled
   accurately. Recompute conservative classification after naming, including conflicts.
5. **AI transparency:** prompt 4.2.0 records per-field validation rejection reasons and
   displays retained-original wording notices. The live synthetic test now requires a
   genuinely changed, validated meaning in both overview and finding, not just fallback.
6. **Progress and duration:** authenticated lightweight progress polling avoids repeatedly
   loading/re-evaluating full reports. Saved-report AI retries remain discoverable after
   dashboard refresh. Two host workers share a global two-process limit and a 30-minute
   host-stage budget; timeouts keep explicit incomplete coverage. AI retains its separate
   15-minute deadline including queue time.
7. **Maintenance and quality:** added offline storage audit, retention preview and explicit
   backup recovery into a new report ID. Existing files are never overwritten by recovery;
   no automatic deletion or database migration was introduced. Full configured Ruff lint
   and formatting now pass; VS Code startup tasks are no longer excluded from sharing.

Verified: **170 offline Python tests, 16 JavaScript tests, 86% Python statement coverage**,
real Edge workflow with synthetic scans, real local Ollama using synthetic facts, and a
fresh installed wheel serving four pages, seven assets and working demo endpoints.
Existing saved scans were not rewritten, deleted, or automatically sent for AI analysis.

**Next session:** at home, confirm the authorised range and one device before a live scan.
Then validate real Pi-hole name extraction with a configured instance. No live scan,
Pi-hole request, DNS lookup or packet capture was run on the unauthorised network.
Ubuntu validation and the nontechnical-reader study also remain pending. Retention is
preview-only; permanent deletion and incompatible-schema migration remain future work.

Restart the old backend using **NetGuard: Start backend** to load the fixes. For historical
reports, use **Prepare this saved report with Ollama**; another network scan is not needed.

## Follow-up reliability and readability fixes (24 September 2026)

- One OS-backed instance lock per data folder now covers startup recovery through
  shutdown. A second instance exits before it can reconcile the first one's jobs.
- JSON and raw-output writes use short, exclusively created temporary filenames.
  Backups are replaced atomically, and scan schema validation happens before writing.
  The previously failing long-path archive test now passes.
- Dashboard refresh resumes the saved scan, including AI preparation and scans that
  finished while the page was closed. Transient polling failures retain the scan ID
  and retry; a refresh never launches a new scan automatically.
- Nmap 7.991 was verified in both local Python environments. The dashboard waits for
  status and distinguishes missing Nmap, storage failure, and expired sessions.
  Session cookies/CSRF are rechecked on page load. Newly resolved scanner paths are
  passed to the supervisor before a scan starts.
- Ollama prompt 4.1.0 prefers reviewed wording for a reader without computing
  knowledge. Every catalogue sentence now has a plain-language alternative. The
  report explains services, priorities and unknowns, displays report-level next steps
  and checks, and includes a glossary. Original evidence/severity is unchanged.
- Verified: 150 offline Python tests; 16 JavaScript tests; real Edge synthetic
  workflow including refresh and expired sessions; local Ollama synthetic report.
  No live network scan was run and existing user reports were not changed.

Restart the backend once to load these changes, using the VS Code **NetGuard: Start
backend** task. Stop the old task first and use the newly printed session link.
For older reports, choose **Prepare this saved report with Ollama** to apply new
wording without another network scan. A live Pi-hole test and human-reader study
remain pending; usability improvements are not a claim of participant validation.

1. **AI in normal report flow — implemented.** Save factual JSON, prepare a report
   overview plus every finding with local Ollama, validate and checkpoint batches,
   and wait in the UI until completion. Empty and failed scans receive an overview.
   AI failures expose factual results and a retry action. Original evidence and guidance
   remain available; legacy AI-off settings no longer skip preparation.
2. **Result-size boundary — implemented.** Equal 20 MiB UTF-8 read/write limits,
   checks before replacement, and separate guidance snapshot archives. A larger primary
   result fails explicitly while preserving existing checkpoints.
3. **Failed results accessible — implemented.** Dashboard opens saved failed reports.
4. **Light known-host Run again — implemented.** Saved host lists are preserved.
5. **Technical output — implemented.** Script evidence keeps up to 1,024 characters,
   with an explicit truncation flag.
6. **mDNS wording — implemented.** Advertisements, discovery responses and service
   responses have distinct labels. Name sources and conflicts remain visible.
7. **Installation and evaluation — partially complete.** Dependency pins reconciled,
   package assets declared, saved-report history implemented, browser automation added,
   storage lifecycle and reader-study protocols written. Actual Ubuntu lab testing and
   the participant study require their environment and participants; neither is claimed
   as complete. See the current verification record for wheel-install results.
8. **Incomplete checks — implemented; live validation pending.** Up to two attempts,
   specific reasons and attempt counts, accurate unfinished counts, and a retry action
   creating a new scan of only eligible unfinished hosts. A live target must be confirmed
   because the saved and detected scopes differed during this session.
9. **Network message — implemented.** Dashboard uses the agreed generic readiness
   message; Settings loads actual configuration/detection and has no static example value.
10. **Device names — implemented for available sources.** Combine Nmap, reverse DNS,
    optional mDNS and Pi-hole labels with provenance, conservative confidence and conflicts.
    A generic router import remains dependent on a vendor API or sample client-list export;
    the evaluation notes explain the required investigation input.
11. **Optional Pi-hole integration — implemented; real instance validation pending.**
    Backend API authentication, scoped DHCP/network names, expiry and MAC matching,
    bounded requests, logout, graceful failure and tests using simulated responses.
    Set `APP_PIHOLE_URL` and `APP_PIHOLE_PASSWORD` before enabling it in Settings.

The existing saved scans were preserved. No SQLite migration, router reconfiguration,
packet capture or background network-wide scan was performed.
