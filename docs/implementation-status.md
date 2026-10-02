# Implementation brief status

## Running app and network recheck — 2 October 2026

Restarted the verified idle old backend and confirmed the current API is running;
41 previous reports were preserved. The later normal home Light run completed
analysis, with one unreachable device retained as incomplete coverage. A subsequent
connection change to the previously unauthorised network is now shown clearly:
Check network again refreshes status without submitting a scan. All 27 dashboard
tests and actual authenticated Chromium checks passed. See [testing](testing.md).
The prior backend-restart handover below is superseded; reload for the final UI change.

## Network recovery — 1 October 2026

All eight steps in the [network recovery plan](network-recovery-plan-20261001.md) are
implemented: Windows gateway parsing, normal saved-scope correction with backup,
Automatic/Manual controls, confirmed-scope admission, actionable mDNS diagnostics,
bounded honest AI readiness checks, Light timing guidance and clearer service labels.
The normal app now uses the authorised `192.168.1.0/24`; saved scan evidence is unchanged.
353 Python and 48 JavaScript tests, three-engine browser checks and fresh packaged
installation passed. Restart the backend after active jobs finish and hard-refresh
for new routes/assets. No new live scan was run during this implementation.

## Library reliability — 1 October 2026

Implemented target-preserving Deep picker refresh, last-check context, separate
unreadable-report warnings, accurate no-match wording and a bounded per-instance
compact search cache. The [execution plan](library-improvements-plan-20261001.md)
records verification and the live-test gate. Reader/physical-device protocols were
extended, not presented as completed evaluations. No new live Light or Sony Deep run
is authorised on the currently connected ANGLIA.LOCAL network.

This is the handover for the eleven agreed items. Verification details are in
`testing.md`; external evaluation steps are in `evaluation.md`.

## Report fixes and Pi-hole scope - 30 September 2026

Implemented stacked unfinished-check notes (including narrow screens), explicit device
addresses on comparison cards, visible name-lookup outcomes and local failure feedback,
and the search label "Search devices and results". A version mismatch now explains how
to restart the backend before starting a new scan; existing-job recovery remains available.
Pi-hole deployment/evaluation is deferred to [future improvements](evaluation.md), not
an outstanding requirement for the current assessment. The inactive connector is retained.
Verification and the requested single-Sony Deep scan are recorded in `testing.md`.
The [Deep run](deep-sony-20260930.md) completed with fresh mDNS naming, 15 open services
and nine review items; original normal reports were preserved in the isolated workflow.

## Experience and discovery improvements - 30 September 2026

All seven steps in [the implementation plan](experience-improvements-plan.md) are implemented:

1. Multiword search across findings and devices, including devices without findings,
   with visible counts and Clear search.
2. Recent saved Light-device choices in Deep setup, with dates, uncertainty and manual entry.
3. Per-job running overview, progress/report links and explicit cancellation.
4. Server-filtered history and optional report titles stored separately from scan evidence.
5. Revision-based nickname updates in already-open, visible finished reports.
6. Explicit, authorised and bounded reverse-DNS/optional-mDNS name refresh with provenance.
7. A visible panel for existing cautious historical comparisons.

Original scan evidence remains unchanged by titles/name refreshes. Optional annotation
failure leaves factual results visible with an explanatory notice. Synthetic regression,
responsive and packaging evidence is recorded in [testing](testing.md). No live scan,
real DNS/mDNS verification, model call, Pi-hole deployment or normal report migration
was performed. Reader evaluation, physical-device checks and large-archive performance
remain external follow-up work. Restart the backend after active jobs finish and reload
the browser to use the new routes/assets.

## Five active jobs with quiet capacity handling - 29 September 2026

Raised the default job limit from two to five. Retained two Nmap process slots and serial
Ollama preparation; more active jobs do not imply five simultaneous scanner processes.
Full pages show a neutral inline waiting status, not a capacity error alert, and poll for
availability before re-enabling Scan. Nothing is submitted automatically. The API still
enforces atomic admission and returns HTTP 429 for races; the dashboard handles it quietly.
Existing explicit APP_MAX_CONCURRENT_SCANS overrides still take precedence over defaults.

## Independent Light and Deep pages - 29 September 2026

Added `/light` and `/deep`, backed by the same template, API and JSON storage. Each page
fixes its profile, has its own pending-job key, and retains its route on refresh. Merely
opening a page does not start a scan or attach to the other profile's job. Pasted links
to a mismatched profile are redirected to the general progress page. Existing root setup
and Run again navigation remain compatible. No second process, SQLite migration or
nickname merger is introduced; existing nickname identity matching/locking remain intact.
Restart an older running backend to register the routes; no running instance was stopped
as part of implementation. See `testing.md` for final verification results.

## Report layout restored; parallel scan tabs - 29 September 2026

At the user's request, first-action guidance is back in the original Understanding your
results card rather than a new panel above statistics. Responsive fixes and factual labels
remain. The dashboard offers a new-tab setup while a job runs; each started tab is pinned
to its own scan ID for refresh/progress/cancel. Light and Deep use the existing shared API,
two-job default admission and bounded scanner resources. No extra backend instance or
database is needed. Ollama preparation remains queued rather than running models in parallel.
See the latest `testing.md` entry for synthetic concurrency/browser verification.

## Usability and release-check improvements - 29 September 2026

Implemented first-action placement, checked/discovered counts, precise completion wording,
stable finding ordering and simpler labels. Original evidence and AI provenance remain
available. Responsive coverage now includes phone/tablet/desktop sizes in Chromium,
Firefox and WebKit, with keyboard, text-size and selected touch-emulation checks.
Added pinned local security gates and a copied-backup recovery drill; updated vulnerable
development test dependencies without changing runtime pins. See the dated results in
[testing](testing.md) and [repeatable release checks](release-checks.md).
No new network scan or change to normal saved reports was required. Physical devices,
real reader-study results, remote Ubuntu CI and actual Pi-hole evaluation remain pending.

## Quality management baseline established - 28 September 2026, evening

The [quality plan](quality-plan.md) now defines project-specific standards-informed
criteria, owners, risk/release controls and executable verification steps; the
[matrix](quality-traceability.md) links requirements to code/tests. The
[new execution record](quality-evidence-20260928.md) contains the subsequent real Light
scan, local Ollama, browser, evidence replay, regression, package and data-preservation
results. It explicitly does not claim ISO certification or completed user evaluation.
No source refactor was needed for this baseline; focused count/mobile and maintainability
improvements are recorded for the next change, separately from pending external checks.

## Dashboard startup recovery completed - 28 September 2026

Reproduced a permanently disabled Checking scanner button when a cached pre-change
module lacks the new setup export. Page scripts and dependencies now use a coordinated
cache-busting version, local responses disable caching, and an independent startup
guard offers Reload page on module failure. API/session requests have a bounded wait
without automatic write retries. Full browser/offline checks passed (306 Python,
31 JavaScript). No scan or backend restart was performed. Hard-refresh the browser;
restart the backend once to enable the new cache headers. See `testing.md`.

## Run again navigation completed; Pi-hole host choice pending - 28 September 2026

Run again now returns Light scans to the starting page. Deep scans first ask whether
to reuse the previous device address or choose another, with Cancel/Escape available.
No scan starts on navigation; users confirm the setup and press Scan. Current scope is
still validated by the backend. Light known-host lists remain visible and reusable.
An active backend scan is resumed rather than duplicated; stale completed-tab storage
does not bounce setup back to the old report.

Verified with 305 Python tests (including synthetic browser workflow), 29 JavaScript
tests and a final mobile-dialog browser rerun. Existing reports are not modified.

Pi-hole app integration is present, but there is no configured service. This Windows
machine lacks Docker/WSL. Await the user's choice of an authorised Linux VM/Raspberry
Pi or Windows container setup before installing system components or creating secrets.
No router DNS/DHCP changes are authorised by this handover. See `pihole-setup.md`.

## Latest fixes and improvements completed - 27 September 2026

1. Browser validation errors show readable field messages, not object strings.
2. Blocked session storage no longer stops startup: an in-memory token and visible
   notice preserve the authenticated request flow. Session expiry remains explicit.
3. Old AI records cannot claim current successful review while their wording is hidden;
   a ready summary requires matching current overview and finding records.
4. Successful Nmap output explicitly recording one unreachable target is distinguished
   from malformed output. Both profiles retain bounded retries and missing coverage.
   No historical result was silently reclassified.
5. Read-only report presentation consistently prefers reviewed plain-language choices,
   including zero-finding reports, while preserving original guidance and AI audit.
   Device cards list observed features. Confirmed web services get address-bar help
   and warnings against credentials over HTTP or bypassing certificate warnings.
6. Saved AI progress records waiting/preparing/finished, total/completed/active counts
   and batch attempt. Refresh restores the counts; fallback records are not counted as
   successfully prepared. Existing reports without this optional field remain readable.
7. Settings/report locks have a five-second acquisition limit. API contention returns
   a readable 503 with `Retry-After`; it does not bypass locks or replace prior evidence.
   Transient background storage contention is not misreported as a scan time limit.

Verified: **306 Python tests, 24 JavaScript tests**, browser workflow, real local Ollama
on synthetic facts, installed wheel, and desktop/mobile review of a prior home report.
All 30 production reports were validated read-only. No new network scan was run.
See `testing.md` for artifacts and outstanding external evaluation.

Restart **NetGuard: Start backend** once to load the backend changes. New host checks
and AI preparation save the new diagnostic/progress fields; reopening saved reports
uses the clearer display without modifying their observations or historical errors.

## Beginner-report implementation brief completed — 26 September 2026

1. Partial AI records remain retryable. Accepted fields/list entries are frozen on
   retry; failures retain original guidance and a visible retry action. A stricter
   reviewed-choice output schema preserves list order and lengths. The existing
   two-attempt batch and overall analysis time limits remain in force.
2. Replaced the count-based red ring with neutral counts and a priority breakdown.
3. Replaced normal-view field paths with ordinary labels. Validation codes are in
   expandable technical details; completed preparation no longer shows a redundant button.
4. Grouped repeated next steps by rule/action and affected devices, made identification
   the first step, reduced repeated card text and duplicate coverage statements.
5. Relevant saved web-upgrade checks appear beside finding explanations for either
   profile, with starting-page/time limitations. They are explicitly saved checks,
   not new AI conclusions; raw metadata and identifiers remain outside model input.
6. Added editable/removable, explicitly user-assigned nicknames in separate local JSON.
   Same-report assignments work without a MAC. Reuse requires a matching network scope,
   a unique matching MAC in both reports, a finished earlier source within seven days,
   and one unambiguous nickname anchor. Editing does not extend the source age.

Verified: **288 Python tests, 18 JavaScript tests**, browser workflow, synthetic local
Ollama, fresh installed wheel, and a disposable copy of the real report. In the latter,
all **16 rejected fields resolved in two requests**, with accepted wording, facts and
the original report unchanged. See `testing.md` for artifacts and limitations.

Restart **NetGuard: Start backend** once to load the changes. Older partly simplified
reports offer **Retry remaining wording** without rescanning. Nicknames are entered via
**Add your own nickname** on device cards; clear the text to remove an assignment.
Nickname changes affect annotations only, never scan evidence or AI input.

No new network scan, Pi-hole installation, SQLite migration, commit or push was done.
Ubuntu/remote CI, live Deep/Pi-hole and participant comprehension remain unverified.
Next checkpoint: review the revised page with nontechnical readers, then confirm the
current authorised home network before any further live collection.

## Remaining implementation follow-through - 26 September 2026

- Added persisted `enrichment` progress before name/detail collectors; dashboard refresh
  resumes this stage without launching another scan. Both scan profiles share it.
- Added clearly rule-based device cards, including unfinished targets with no parsed
  device result. Historical names, conflicting names and coverage limits remain explicit.
- Ollama retries only rejected items, preserving accepted text. An invalid batch does
  not suppress attempts for later findings; outages and overall deadlines remain bounded.
- Nmap validation failures now include reviewed diagnostic text. The previous live host
  failure cannot be reconstructed without its missing raw output; no cause is invented.
- Added pinned-action Windows/Ubuntu CI and a fresh installed-wheel verifier. No commit,
  push or remote CI run was performed; Ubuntu validation remains pending.
- Added a participant-session guide and empty results template. No participant study
  has been conducted. Pi-hole still requires an actual installation for live validation.

Restart the backend once to load the changes. No running user app was restarted and no
saved user reports were modified. This work used synthetic scans and local Ollama, not
a new home-network scan. See the newest testing entry for exact verification results.

## Naming reliability follow-up - 25 September 2026

Compared the two latest user reports: both had 11 devices, but names fell from three
to two because the TV's mDNS advertisements were absent in the newer report, despite
the same recorded MAC. No collected advertisement was dropped at name assignment and
the eight-host cap was not reached; timing is a plausible contributor, not a proven
sole cause. mDNS collection now uses nonblocking concurrent lookups, a four-second
window and a bounded retry. Friendly-name TXT data and advertised hostnames supplement
instance labels. Recent direct names can be reused only as visibly historical labels
under same-scope/MAC, age and ambiguity guards. See the latest testing entry for results.

## Follow-up review and organisation - 25 September 2026

Fixed four confirmed edge cases: empty UPnP metadata, history comparisons with missing
port selections, optional failures mislabelled as timeouts (and blocking another lookup),
and guessed service identities increasing device-type confidence. Each had a failing
regression test before its fix. Enrichment coordination now lives in `jobs/enrichment.py`;
pure fact formatting lives in `scanner/observations.py`, separate from network requests.
All application modules remain referenced; no source files or saved reports were deleted.
See the newest `testing.md` entry for the final rerun and remaining external validation.

## Richer Light and Deep device information - 25 September 2026

Implemented the six agreed additions in the shared pipeline: richer optional mDNS,
conservative evidence-based device types, bounded UPnP descriptions, HTTP-to-HTTPS
checks and certificate dates, selective NetBIOS names, and recent-report comparisons.
Both profiles collect and display these under **More about this device**. Deep remains
single-host; advertised services never become confirmed open ports merely from an
announcement. Limits and failed optional checks are explicit. Local JSON and existing
reports are preserved; no Pi-hole service was installed or configured.

See the current verification entry in `testing.md`. Earlier live results below predate
these richer collectors and must not be treated as their live-network validation.

## Latest live check — 25 September 2026

Home Light scan and Ollama processing now verified: all 12 discovered device checks
completed, with 13 open services and 8 review items. See [results and follow-ups](live-check-20260925.md).
Pi-hole is still not installed/configured here; no live name extraction is claimed.
The check found a timing-sensitive test and user-facing AI fallback wording to improve.
This was a verification pass, not another application-code change.

## Pi-hole setup implementation — verification deferred (25 September 2026)

Prepared `deployment/pihole/compose.yaml` and its opt-in home DNS profile. The base
deployment is loopback-only, requires a private administrator-secret file, disables
DHCP/NTP serving and does not restart automatically. No container/runtime was installed
or started. NetGuard now supports `APP_PIHOLE_PASSWORD_FILE`, sanitised setup errors,
clearer unverified-connection wording, and a manual VS Code Pi-hole launch task.
See [setup and rollback](pihole-setup.md).

New regression tests cover password files and configuration-only status/settings;
test fixtures no longer inherit real Pi-hole credentials. **No tests, scans, app starts
or Pi-hole requests were run for these changes**, at the user's request. The earlier
passing results below predate this implementation.

Prepared lockfile updates: platformdirs 4.11.13, Uvicorn 0.54.0, Ruff 0.16.9. They have
not been installed or validated in the virtual environments. Existing constraints allow
them. Major dependency/test-client migrations and CI automation remain follow-up work,
not silently included in an untested runtime upgrade. Saved-report AI preparation,
real Pi-hole name extraction, home scans, Ubuntu and reader evaluation are deferred.

## Latest code organisation/recheck

The subsequent full review is in `architecture.md`; cleanup and repeatable commands are
in `workspace.md`. Added strict cache projections with fallback to saved evidence, fixed
device ownership on report recovery, and removed duplicate/blocking scope detection.
Shared status definitions were consolidated without rewriting the overall architecture.
Latest checks: **187 Python tests, 16 JavaScript tests, browser/local Ollama, lint,
formatting and installed-package verification passed**. Saved data and Git work were
preserved. Fifty old generated folders were archived and removed; the empty `front end`
folder is locked by another process and remains. Historical notes/screenshot are organised
under `docs/archive/` and `docs/reference/`. Live network testing is still deferred.

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
