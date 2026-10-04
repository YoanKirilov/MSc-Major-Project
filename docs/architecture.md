# Architecture and workspace review

For the current structure, read [Current architecture](architecture-current.md).
The dated sections below are historical review evidence and may describe superseded behaviour.

## Latest live review — 2 October 2026

The [live-check record](live-check-20261002.md) supersedes older test counts and
network-observation snapshots below. The JSON/FastAPI/job/provider separation remains
intact. CVE button eligibility is now presentation metadata computed by the exact
backend lookup policy, not a second partial implementation in JavaScript. Evidence
files are unchanged by report rendering or reference lookup.

The latest review identified two follow-ups: conservative resolution of renamed CVE
product identifiers, and explicit handling of laptop sleep during long scans.
Neither should be hidden by reporting missing checks as successful. The new source
layout test protects template/static import reachability alongside Python imports.

## CVE references — 2 October 2026

The new `api/cves.py` route performs user-requested research on a saved service.
`scanner/cve.py` handles conservative CPE selection and bounded NVD requests;
`explanations/cve.py` validates Ollama's reviewed match-context wording. Typed results
live in `schemas/cve.py` and the existing annotation store, separate from scan facts.
`static/js/cves.mjs` renders source links and explicit lookup controls. The live
scanner and rule engine do not treat a CVE candidate as an assessed vulnerability.
See [CVE flow and limits](cve-references.md). The current asset tree has nine JS modules.

## Source organisation review — 2 October 2026

The existing separation of API boundaries, job orchestration, scanner collectors,
JSON storage and AI validation remains appropriate. Import and asset traversal found
no unreferenced application module, template or JavaScript file. Removed only a
disused discovery-parser wrapper, obsolete score-ring/icon styles and a redundant
report-formatting wrapper. Framework-registered callbacks, demo APIs and the optional
Pi-hole connector remain active or intentionally supported. Generated build/cache
folders were archived separately; see [workspace organisation](workspace.md).

## Network recovery — 1 October 2026

Scope precedence is unchanged: saved manual range, backend configuration, then a
bounded detected private range. Settings present explicit Automatic/Manual choices
without changing the JSON schema; selecting Automatic clears the saved override.
Backend configuration still takes precedence over detected scope and is shown in the UI.
Windows parsing accepts IPv4 gateways following an IPv6 continuation while rejecting
gateway-free virtual adapters and ambiguous multiple networks.

New dashboard scan requests include `confirmed_scope` when the backend advertises
`scope_confirmation_supported`; the API rejects a changed scope before creating a job.
Automatic mode asks permission on every scan rather than remembering authority by CIDR,
because distinct networks can share a range. Legacy clients retain existing explicit
authorisation and scope validation. Interface diagnosis distinguishes unmatched scope,
unavailable selection, multiple matches and a failed Nmap interface-list command.

The local Ollama provider records readiness separately from model generation: ready,
missing model, unreachable, unresponsive, or error. A timeout is not proof of startup
or a missing model. Status caches unsuccessful readiness for five seconds; the dashboard
can recheck an unresponsive service at most three times at 30-second intervals. Settings
offer a manual recheck. Original analysis deadlines/fallbacks and evidence are unchanged.
Progress projections gain optional `started_at` for elapsed-time display; old projections
continue to validate. No estimated finish time is promised.

## Library reliability update — 1 October 2026

History separates unreadable-file warnings from filtered results/counts. Recent-device
choices carry last-check and reachability context, without treating mDNS or completed
checks as proof of safety. Picker refresh preserves the entered target and explicitly
explains retained addresses missing from the refreshed list.

Each `JsonStore` owns a thread-protected `LibraryCache` of compact, read-only search
projections. It retains at most 512 reports and 8 MiB of serialized projection data
(Python object overhead is additional), never full XML/AI/evidence. Scan/terminal file
mtime, ctime, size and inode changes invalidate entries; unstable reads and failures
are not cached. Titles and nicknames are loaded separately on every request, retaining
revision/identity semantics. Restart rebuilds the cache; source JSON is authoritative.
This improves repeated searches within the cache budget, not cold-load or unlimited
archive performance. Directory/summary enumeration and nickname-anchor reads remain.
No SQLite or additional persistent search index was introduced.

## Previous architecture review

Reviewed 28 September 2026. This is the current map; dated build snapshots under
`archive/` and older testing entries are historical, not the current implementation.

## Report usability follow-up - 30 September 2026

The status API exposes `ui_contract_version: 1`. Dashboard setup checks compatibility
before admitting a new scan from the page and explains when a backend restart is needed.
Recovery of an existing pinned/running job takes precedence so a stale backend warning
does not strand active progress. Coordinated module version `20260930-report-fixes`
loads the matching interface assets; the server's scope/admission checks are unchanged.

Unfinished-check notes use a stacked block layout; comparison cards include the address
alongside the saved name. Identification retries show pending, returned-name, empty and
failure feedback on the affected card, while preserving original identity and evidence.
Pi-hole deployment and live evaluation are now deferred future work by project decision.

## Report library and discovery helpers - 30 September 2026

`app/api/library.py` owns authenticated history search, recent-device choices, running-job
summaries, report titles, nickname revision snapshots and explicit name refresh. Mutations
retain session/CSRF checks. `app/storage/library.py` filters saved live reports before
pagination; optional nickname/title corruption produces warnings rather than hiding the
factual report. Search currently reads report JSON and is not indexed or benchmarked for
large archives. The picker reads recent Light reports in the configured scope, does not
probe devices and cannot establish that an old address still belongs to the same device.

`app/storage/annotations.py` keeps titles and later name claims in per-report
`annotations.json` with a previous-version backup, bounded atomic writes and the existing
per-scan lock. Title edits use optimistic revisions; name refresh merges the latest saved
annotations. These operations do not rewrite `scan.json`. Nicknames remain in the shared
nickname store with existing identity/revision safeguards.

`app/scanner/name_refresh.py` performs only bounded reverse DNS and optional mDNS for an
explicitly selected address. The API revalidates scope/interface, requires authorisation,
rejects concurrent refreshes using an application lock and applies a ten-second overall
deadline. Announcements are unverified claims, never new findings. The operating-system
DNS resolver may outlive the async timeout in its worker thread. No automatic port scan,
packet capture, Pi-hole refresh or model request is introduced by this action.

`setup-tools.mjs` owns recent-device setup and the four-second visible-page job overview.
Finished visible reports check nickname revisions every eight seconds without resetting
search/selection. Titles and later name annotations are not pushed between open tabs.
The report comparison panel presents existing saved history observations rather than
recomputing findings. One backend, five-job admission, two scanner slots, serial Ollama
and JSON storage are unchanged. Verification and external limits are in [testing](testing.md).

## Concurrent dashboard tabs - 29 September 2026

Follow-up: `/light` and `/deep` render the same dashboard template with a fixed profile,
avoiding duplicate UI implementations. Each has a profile-specific pending-session key
and retains its own page path when pinning a scan UUID. New dedicated pages do not
automatically resume arbitrary backend jobs. A pasted UUID is checked against saved
profile metadata; a mismatched profile redirects to the generic progress page. Shared
nickname/settings/report storage and backend authentication/admission limits are unchanged.

The supervisor now admits five jobs by default and shares a two-process Nmap limit.
`/api/status` exposes the actual admission availability separately from active analysis
retry tasks. Full setup pages poll this read-only status every three seconds and quietly
disable Scan until a slot becomes available. An admission-race HTTP 429 follows the same
inline waiting path; no automatic POST retry or unbounded job queue is introduced.
The UI now exposes an explicit new-tab setup (`/#setup=1&new=1`) which does not attach to
another active job or reuse a copied pending-session key. A started/resumed tab is pinned
to `/#scan=<uuid>`; this takes precedence over session storage on refresh. When there are
multiple jobs and no selected job, show explicit resume links instead of selecting the
first. Status/progress/cancel/results retain the existing authenticated per-ID API routes;
no duplicate server, new store or relaxed instance lock is introduced. AI preparation
remains serial. Restored the previous report guidance placement without removing responsive
or evidence-clarity fixes. Browser regressions use synthetic scanner output only.

## Overall assessment

The standards-informed [quality plan](quality-plan.md),
[traceability matrix](quality-traceability.md) and
[new baseline record](quality-evidence-20260928.md) now define measurable checks and
remaining release work. The latest organisation review found no unused shipped
modules/assets through import and asset traversal. It recommends bounded future
extractions in the scan supervisor, report rendering and AI orchestration, not a
framework migration or broad rewrite. See the record for exact limits of this review.

The design fits a local, single-user research prototype. Collection, deterministic
findings, AI wording, persistence and browser presentation are separate layers.
It is **not** a production multi-user service: do not expose it to the internet or
run several server workers against one data folder. No database migration is needed
for the current scope; JSON remains the storage format.

The Pi-hole connector/setup configuration has synthetic regression coverage; actual
Pi-hole deployment and name extraction remain **unverified**. Deployment files are
under `deployment/pihole/`, separate from the Python package; backend credentials may
come from a bounded private UTF-8 file. Status reports local configuration errors, not
connection health, and never probes Pi-hole. See [deployment boundaries](pihole-setup.md).
The Pi-hole service itself has not been installed or activated by this change.

```text
Browser templates + JavaScript
    -> authenticated API (session, CSRF, authorised scope)
    -> ScanSupervisor (bounded jobs, cancellation, retries)
         -> Nmap runner -> XML parser -> deterministic rules
         -> optional mDNS / Pi-hole naming
         -> bounded web / UPnP / selective NetBIOS details
         -> conservative classification + recent-report comparison
         -> saved JSON checkpoints
         -> local Ollama -> source-bound wording validation -> saved report
    <- lightweight progress while working; full report when finished
```

## Code ownership

| Area | Responsibility |
| --- | --- |
| `app/main.py`, `cli.py`, `config.py` | Assemble dependencies, own the instance lock, select configuration |
| `app/api/`, `security/` | HTTP/session boundaries, scope validation and user actions |
| `app/jobs/` | Job lifecycle, host workers, checkpoints, cancellation and AI deadline |
| `app/scanner/` | Fixed Nmap commands, bounded subprocesses, safe XML, name sources and bounded device-detail collectors |
| `app/risk/`, `profiling/` | Factual findings, original guidance and cautious device hints |
| `app/explanations/` | Redacted structured input, Ollama, reviewed wording and fallback audit |
| `app/schemas/` | Primary data and validated history/progress projections |
| `app/storage/` | Atomic JSON, locks, bounded files, archives and explicit recovery |
| `app/templates/`, `static/` | Four page types (six routes), shared layout, CSS and nine active JS modules |
| `app/demo/` | Fictional demonstration data; separate from real scan observations |
| `tests/`, `scripts/` | Automated checks, installed-package verification and cleanup tooling |

All five HTML templates, nine JavaScript modules and the stylesheet are referenced by
active pages/imports. The asset-traversal integration test checks that every shipped
static file is reachable. All substantive Python modules are reachable from the app/CLI;
package initialisers are retained. No live source module was removed just because it
looked unfamiliar or had no direct HTML reference.

## Implemented follow-up improvements - 27 September 2026

The latest run passed **306 Python and 24 JavaScript tests**, including a synthetic
browser workflow and real local Ollama. The installed wheel and read-only desktop/mobile
view of the previous home report also passed. See `testing.md` for exact artifacts.

- `explanations/presentation.py` creates response-only plain-language views from the
  existing approved choices. It does not rewrite evidence, model output or prompts.
  Original guidance stays expandable; editorial choices are not labelled new AI output.
- `AnalysisProgress` is optional in schema-v1 reports and their polling projections.
  AI checkpoints persist waiting/preparing/finished, total/completed/active counts and
  attempt number. Only accepted complete records count as prepared; retries reuse them.
- Shared browser API code formats validation arrays and guards browser storage access.
  The in-memory token fallback retains CSRF checks and does not conceal expired sessions.
- AI status wording checks the overview and finding records, including prompt versions,
  before claiming that the displayed report has current successful AI review.
- Nmap zero-host output explicitly reporting one down target raises `HostUnreachable`;
  absent or contradictory counts remain invalid output. Failed checks stay unassessed.
- JSON settings/report lock acquisition is bounded at five seconds. HTTP contention
  returns 503 with `Retry-After`, not a forced write. Locks are never bypassed; persistent
  external contention must be resolved before further writes can succeed.

No new network probes were introduced by the clearer web-page instructions; they are
plain text derived from saved probed web-service facts, with HTTP/certificate warnings.
Historical scan errors are retained as recorded, even where new runs classify them better.

## Earlier end-to-end recheck - 27 September 2026

Reviewed startup/instance ownership, session and scope boundaries, job lifecycle,
optional collectors, JSON checkpoints/recovery, AI validation and browser presentation.
The final Windows check passed 290 Python and 18 JavaScript tests, including synthetic
browser workflow and real local Ollama. Statement coverage was 88%; this is not proof
that all branches, operating systems or real-network outcomes are covered.

Moved the pure sentence validator into `explanations/validation.py`, leaving batching,
provider calls, retries and persistence in `service.py`. The validator body is unchanged;
the service keeps its prior static entry point. Prompt/version, approved wording and
stored evidence are unchanged. New layout regressions verify this delegation and that
all substantive Python modules are reachable by imports from the CLI entry point.
Together with the existing asset traversal, no unused application file was identified.

No new blocking regression was found in these checks. The then-open zero-host Nmap
classification and beginner-language/action gaps are resolved by the follow-up above;
`live-check-20260926.md` records the original observations. Saved reports were checked read-only, and the previous
live report was reopened on desktop/mobile. No new network scan was performed.

## Earlier review fixes (25 September 2026)

- Malformed cached progress/history could raise an error or hide a readable report.
  Caches now have explicit schemas and fall back to the authoritative saved document.
- Managed JSON now rejects non-object roots and non-finite numbers, as well as duplicate
  keys. Invalid cache files cannot masquerade as valid report status.
- Recovered reports now update each device's containing report ID. Stable device/service
  identifiers and the original report are preserved.
- Network scope selection is now a pure operation on one existing network observation.
  API requests no longer launch a second synchronous detection command on the event loop.
- Shared status types and terminal-update fields have one definition instead of duplicates.
- The old build-state file and screenshot have been moved into historical/reference docs.
  Old generated outputs are archived; future checks use one ignored artifact directory.

## Safety and AI boundaries

The readability follow-up separates output-schema construction (`explanations/format.py`),
field-preserving retries (`explanations/retries.py`), pure acceptance validation
(`explanations/validation.py`) and pure display helpers
(`static/js/presentation.mjs`). `wording_schema` 1.0.1 is stored alongside prompt 4.2.1;
the reviewed source choices are unchanged, so accepted wording can remain cached.
Partially accepted records retain accepted fields but keep analysis retryable until
all rejected fields resolve or the bounded attempt/time budget ends. Original factual
guidance remains available on failure. The provider schema narrows generation; the
application's source-bound validation remains the acceptance boundary. See the
[Ollama structured-output interface](https://docs.ollama.com/capabilities/structured-outputs).

Nicknames live in `nicknames.json` with a revision, cross-process lock, atomic replacement
and previous-version backup, bounded to 200 assignments of 80 characters each. A
session/Origin/CSRF-protected PUT endpoint edits annotations. Report responses expose
them separately from devices; scan JSON and AI payloads are unchanged. Same-report
assignments use explicit device IDs; cross-report reuse requires scope, unique MAC,
an earlier finished anchor within seven days and no ambiguous assignments. Name-source
metadata remains intact. Invalid nickname storage does not hide a readable scan report.

Ollama selects reviewed plain-language alternatives; it is not an autonomous scanner or
a source of new vulnerability claims. IPs, MACs, hostnames and raw XML stay out of model
input. Severity and evidence remain rule-owned. Rejected wording has field-level reasons;
an unavailable model must not hide factual results. Validation tests and one real local
model check do not establish comprehension by nontechnical readers.

Pi-hole is an optional external name source, not a replacement scanning engine. DHCP and
network-history failures are isolated. Historical names require a matching observed MAC;
names alone never establish reachability or identity. Real instance verification is pending.

### Shared Light/Deep enrichment

`jobs/enrichment.py` schedules and saves optional details after Nmap, before Ollama.
`scanner/details.py` owns network requests; `scanner/observations.py` owns pure evidence
interpretation and bounded `DeviceDetail` formatting. History comparison imports the
pure helper, not the HTTP collector. Both profiles use this path. mDNS observations are reused;
known-host mode browses with an explicit host filter, applied before the discovery cap.
No additional host is added to a Deep scan. Announcements and UPnP descriptions are
labelled as device claims; only Nmap evidence determines service-check coverage.

Two extra-information workers share a 30-second scan budget. NetBIOS also uses the
existing global Nmap capacity. Cancellation stops pending collectors, keeps completed
facts, and discloses missing extras. HTTP checks use HEAD, disabled proxy inheritance,
verified TLS, and at most one explicitly validated same-IP redirect. UPnP GETs are
same-IP only, bounded to 64 KiB and parsed with defusedxml. Arbitrary TXT fields,
UPnP serial numbers, embedded-device names and NetBIOS usernames are not retained
by these collectors. Details are deduplicated and capped at 48 with a visible limit note.

`profiling/history.py` compares at most ten recent live reports without modifying them.
It requires matching scope and a nonduplicated MAC for a possible identity match, and
equal profiles/port selections plus completed checks for service differences. It does
not claim that a MAC proves identity, a changed service proves an attack, or no prior
match means a newly connected device. Existing schema-v1 reports load with empty detail
lists; no destructive migration is needed. Identity metadata stays out of Ollama input.

The follow-up review fixed empty UPnP fields aborting optional checks, missing port
metadata being treated as a comparable history profile, and collector errors being
labelled as timeouts. Independent optional collectors now continue after a source fails.
Only probed open-service identities can strengthen a device-type suggestion; names
inferred from the port number do not count as confirmed evidence. New reports record
enrichment version 1.0.1 and profiling version 1.1.1. Earlier reports remain unchanged.

The naming-reliability follow-up replaces blocking mDNS callback lookups with a bounded
async browser: four seconds, four lookup slots, 750 ms per attempt, at most two attempts
for each of 64 service instances. Cancellation closes the browser and all pending lookups.
Explicit friendly names are preferred over generated service instance IDs; advertised
hostnames provide a fallback and RAOP hardware prefixes are removed from display labels.
If no current name is available, history may supply a clearly labelled previous name
from a direct observation within seven days, using the existing scope/MAC/duplicate guards.
Historical labels retain original dates, never extend their lifetime through copies,
never override fresh names or influence device type, and preserve prior conflicts.

The async API is documented in the [python-zeroconf reference](https://python-zeroconf.readthedocs.io/en/latest/api.html).

## Remaining limitations and recommended order

1. **Verify the implemented fixes in future authorised use:** zero-host classification,
   consistent beginner wording, web-page instructions and saved AI counts are covered
   by automated checks and retained-evidence replay. This pass did not run a new scan.
2. **External validation:** the 26 September Light checks exercised the richer collectors;
   see their dated report. Controlled Deep/lab verification, actual Pi-hole when installed,
   and the intended Ubuntu setup still need evidence. No new live scan ran in this review.
3. **Reader evaluation:** run the documented nontechnical-user study; retain evidence of
   what people understand, not only model/test success.
4. **Continuous checks:** `.github/workflows/checks.yml` defines offline, synthetic-browser
   and installed-wheel checks on Windows/Ubuntu with Python 3.12/3.14. It must still run
   after commit/push; a passing local Windows run is not a Linux compatibility claim.
5. **Maintenance scale:** JSON checkpoints rewrite full documents. History uses caches but
   still enumerates report folders. Retention is preview-only; export/import, permanent
   deletion, incompatible-schema migration and a maintenance UI remain future features.
6. **Targeted refactoring:** the supervisor, explanation service and scan-page controller
   are the largest modules. Extract host execution, analysis scheduling and report rendering
   when extending those areas, under existing regression tests; a wholesale rewrite would
   not itself improve correctness.
7. **Dependency upkeep:** current tests emit pytest-asyncio/Python 3.14 and Starlette test
   client deprecation warnings. They are not runtime failures, but should be resolved before
   upgrading Python/framework versions. Keep runtime and development locks aligned.
8. **Progress/readability:** a persisted `enrichment` phase now displays "Gathering device
   details" before AI starts, including after refresh. Rule-based device cards precede
   the technical table and include failed targets without parsed device records.
   Evaluate readability with the reader-study kit rather than assuming it is proven.

AI retries regenerate only rejected items, preserving accepted items from that batch.
An invalid-output batch does not prevent later batches being attempted; provider outages
still stop after the bounded retry. The existing overall analysis deadline remains in force.
Nmap parser failures retain reviewed, safe diagnostic text without exposing raw output.

## Data checked, not rewritten

The latest audit of the configured data folder found 30 readable, unchanged reports
(17 completed, eight partial, three failed, two cancelled). The earlier audit of the
historical `.preview-data` found 63 readable reports,
including old queued/running records; it is not the active job queue and was not reconciled.
Referenced guidance JSON is readable and device/report IDs match in both sets.
This checks storage consistency, not the truth of historical network observations.

See `testing.md` for exact verification and `storage-lifecycle.md` for recovery instructions.
