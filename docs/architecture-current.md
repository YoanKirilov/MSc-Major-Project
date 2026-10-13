# Current architecture — updated 13 October 2026

The [stable home-progress fix](home-progress-position-20261013.md) keeps progress
below setup on start/reconnect without automatic scrolling. Idle and running setup
share top-aligned layout. Pinned-job recovery and the scanning contracts are unchanged.

[The accessibility/reveal change](report-accessibility-20261013.md) supersedes
eight-entry history loading and paragraph alignment. History reset/open/search
now requests and renders no reports; intentional scrolling admits one entry at
a time, with gesture locking and an explicit keyboard alternative. Recorded
profile colours override visited-link colour and reverse on hover/focus.

`static/js/appearance.js` restores allowlisted Dark/Light, text size and movement
choices from bounded, versioned browser storage before the stylesheet. Native
controls bind on DOM readiness and update root datasets. Device reduced motion
always takes precedence. Display preferences are separate from scan facts and
per-report reading state; old alignment is ignored without losing searches or
disclosures. Light surfaces and severity/text colours are theme-aware. No scan,
job, provider or JSON-storage contract changes were needed.

The [home/history usability change](home-history-ux-20261012.md) consolidates the
home-page scan choices, target controls, readiness and primary action. Duplicate
Light/Deep navigation links are removed; their routes remain compatible and tabs
still observe separate jobs. `static/js/history-feed.mjs` owns bounded one-entry
pagination, submitted-filter snapshots, stale-response rejection and append retry.
The history controller appends on downward scrolling or explicit Show next report; it does
not chain requests on initial layout or after a response. Loaded entries remain in
the native list. Existing authenticated `/api/reports` pagination and whole-library
matching are unchanged; this is progressive rendering, not a new database/index.

The latest [final-wording/layout follow-up](report-layout-final-wording-20261012.md)
removes duplicate original/previous prose from the per-item interface, not from
saved findings/exports. Only accepted final wording or reviewed fallback is rendered.
Supporting disclosures share a desktop row and wrap on narrow displays; open panels
use a wider row with bounded prose. Header/main/footer now share a 1360-pixel shell
token. Filtered review counts are polite status messages; empty task feedback no
longer points to nonexistent controls. Scanner/storage/AI contracts are unchanged.

The 12 October reading follow-up adds retryable storage-read responses for scan/
progress endpoints, exact full-address identity search, and explicit unchecked-device
previews. Each device has one grouped feature-evidence disclosure beside its identity
details; individual feature rows remain compact. The earlier alignment control
was replaced by the 13 October appearance preferences. Existing evidence, revision safeguards,
job limits and JSON storage are unchanged.

Purpose-first titles, visible conditional feature help, first-action web precautions
and the existing glossary support novice reading. The revised approved Ollama wording
uses prompt 4.3.0; older saved wording is not silently treated as newly validated.
The upstream Windows transport-close warning remains under investigation.

The later [same-day UI/UX repeat](ui-ux-live-followups-20261012.md) adds a bounded,
per-tab device filter for review items, saved checklist-status counts visible before
expansion, accurate task-availability wording and filter-scoped disclosure controls.
Repeated unidentified connection replies receive shared context without merging
findings/actions. Technical tables retain readable minimum column widths inside a
labelled horizontal-scroll container. Display state never changes report evidence.

This is the current structural reference. Dated reports and the historical sections
of architecture.md are evidence logs, not current feature/test-count specifications.
See [UI/UX repeat execution](ui-ux-live-followups-20261012.md) for the latest presentation
changes and verification. home-live-review-20261008.md records earlier actual home
scans; offline-code-review-20261008.md records the earlier work-session
organisation. No work-network scan ran; the later home range was explicitly confirmed.

The later [eight presentation follow-ups](ui-ux-followups-20261009.md) add bounded
per-tab reading-state restoration in `static/js/report-view.mjs`, separate from scan
state, evidence and revision-safe editing. The controller restores display settings
only after report facts load. Shared title presentation and device-result matching
prevent inconsistent review labels and duplicated matched announcements. Progress
uses a concise milestone status, not an entire per-second live region. Navigation
offsets track actual height and stop sticking on small/enlarged layouts.

One loopback FastAPI backend owns one JSON data folder through an OS instance lock.
Authenticated/CSRF-protected routes validate bounded authorised private targets.
Light/Deep pages share the backend and nicknames; up to five unique jobs are admitted,
including saved-report AI retries. A scan and its automatic analysis count once;
extra retries receive inline retryable feedback before saved state changes.

`jobs/supervisor.py` owns persisted lifecycle/checkpoints and cancellation;
`jobs/scheduling.py` supplies bounded queue waits and active execution budgets.
`jobs/transitions.py` contains pure failure, queue-expiry and restart report
transformations, separated from orchestration. Admission rejects an already-active
scan ID before replacing its task or cancellation tracking.
Discovery and host processes share two slots. AI has its own serial capacity and
separate queue/execution limits. Browser refresh observes the existing job, never
resubmits it. `jobs/enrichment.py` owns optional bounded device enrichment.
Schema and standalone scope validation share a 254-address maximum for selected
Light hosts, with bounded input strings. Deep remains one explicit authorised host.
On connection the controller reads saved metadata, restores the immutable target,
disables setup and keeps progress below setup. Starting, reconnecting and polling
do not automatically scroll the page.
Progress responses add live backend contact and scanner-process lifecycle activity;
these are not persisted completion estimates or proof of remote responsiveness.

`scanner/network.py` reads structured Windows connections and Nmap adapter data;
new live jobs retain a network context and bind the validated adapter. A monitor
and pre-step checks stop work when the context changes or execution is suspended.
Overlapping Windows adapter queries are shared across jobs/status calls; later
requests read afresh. Guards share overlapping checks and retain distinct failure
reasons for unavailable snapshots versus confirmed changes. Safety-triggered host
cancellation retains its cause. All failures still stop probing.
Windows reads now join connected IPv4 interfaces, addresses, default routes and
network profiles in one bounded process instead of the slower aggregate query.
Cmdlet errors stop the query, typed validation rejects malformed/ambiguous output,
and enumeration order is canonical. The eight-second query deadline, fresh later
reads and failed-closed guard remain; successful home retesting does not establish
that Windows can never time out under other conditions.
These are best-effort local checks, not an atomic network isolation mechanism.
On Windows, an exact self-target from this verified snapshot uses Nmap's automatic
local routing for host/NetBIOS checks. Discovery, remote targets and the network
guard retain the bound interface. A report note distinguishes self-observation
from what another device can reach. Pre-cancelled process work returns without
spawning; cancellation-watcher cleanup is awaited.
`scanner/runner.py` bounds subprocess output and cleanup through the public asyncio
protocol/transport API, including pipes retained after a parent exits. Windows
cleanup stops the direct child and closes owned pipes, not arbitrary descendants.
`runtime_diagnostics.py` observes event-loop errors without suppressing them and
restores the previous handler on shutdown. The Windows socket-shutdown reset is
diagnosed but remains a runtime follow-up, not a repaired application defect.
Linux context currently includes the selected adapter/address and default subnet;
the authorised Ubuntu lab still needs validation.

Nmap XML is parsed to typed observations; deterministic rules create findings.
Attempt metadata and optional per-attempt XML support diagnosis. mDNS adds unverified
advertisements and names, never proof of an open service. Already-discovered hosts
do not consume the eight-new-host advertisement allowance. Pi-hole is deferred.

Ollama receives selected, identifier-free facts and reviewed alternatives. Accepted
fields take precedence in the report; rejected, stale or unavailable model fields
use reviewed plain language. Original evidence and guidance remain accessible.
UI and report explanations count unfinished selected/discovered device checks,
including cancellations and unstarted checks, not just the failure counter. Silent
discovery addresses are excluded. Prompt version 4.3.0 invalidates older AI wording.

`scanner/cpe.py` supplies pure versioned, sufficiently confident application-CPE
eligibility to APIs and the lookup client. `scanner/cve.py` queries NVD only on request
and retains compatibility helper imports. `scanner/cpe_identity.py` uses the pure
validator directly and consults the dictionary after an empty
lookup, rejects ambiguous/incomplete matches and retains resolution provenance.
A unique product/version under another vendor is explicitly a research candidate,
not an asserted identity. Public references are annotations, never scanner findings.
`static/js/notes.mjs` owns revision-aware, full-snapshot projection. It synchronises
titles, every checklist control, later name lookups, CVE panels and recovery notices
in place. Older delayed responses are rejected, even after a failed read; adoption
does not rebuild selected items, filters or expanded device cards. Lookup-button
focus is restored after temporary disablement. Notes I/O errors use readable 503
responses; unreadable/stale/invalid edits use 409 without resetting notes.

`static/js/nicknames.mjs` separately validates and adopts global nickname snapshots.
Acknowledged edit revisions fence delayed polls before a new full snapshot arrives;
older or malformed full-report/poll replies cannot regress labels or notices. Compact
progress is never projected as a full report. Conflicts reload without automatically
retrying a write, and updates preserve filters, expanded device/checklist sections
and keyboard focus. This display projection never changes detected names or evidence.

JSON saves use bounded reads/writes, atomic replacement, revision checks and recovery
checkpoints. Offline export/restore uses checksummed new folders, never overwrites
existing evidence, and excludes session secrets. Retention is a preview, not deletion.
Report annotations can recover a validated previous copy under the scan lock;
corrupt primary bytes are quarantined, revisions advance and the UI discloses
possible lost edits. Invalid backups do not silently reset notes. Quarantined
annotation files are included in offline exports.
Nicknames now use the same recovery principle under their global lock, with readable
storage failures and recovery notices in reports/history. `storage/recovery.py`
reserves a persistent revision fence before publishing recovered notes or nicknames;
repeated recovery cannot reuse a revision held by a stale editor. Both fences and
bounded quarantines (five per document) are included in offline backups. Invalid,
unsafe or oversized copies require manual attention, not silent resets.
Per-action user checklists live in `annotations.json`, keyed by saved finding/action
IDs. The authenticated, CSRF-protected update route requires a finished live report,
a valid saved action and the current annotation revision. To check is the default;
Checked and Need help are saved user notes, not verified fixes. Writes use the same
scan lock, bounded atomic replacement and previous-copy recovery as report titles;
they do not modify scan evidence, AI wording or severity. Stale-tab edits are rejected
and the latest notes reloaded rather than automatically overwritten.
Address-specific checklist labels distinguish unnamed or identically named devices.
Your review progress counts unique actions across the report; its status filter hides
whole task rows in the complete checklist, not observations or the selected item's
guidance. It is not scan coverage, a safety score or
proof of a repair. New reports do not inherit Checked.

Templates and static modules remain reachable. No unused source files were removed.
Shared header/footer includes give all six page types the same navigation and keyboard
bypass. Package data explicitly includes those templates. CSS is grouped by component
and responsive behaviour, with shared spacing, field, error and focus styles.

`static/js/scan.js` owns report state, API requests and revision-aware editing.
`devices.mjs` renders consistent device summaries and preserves nested disclosures/focus;
`finding-list.mjs` reconciles stable review buttons and places the selected explanation
immediately after its row on narrow screens; `editor.mjs` owns labelled modal editing,
validation and focus return. Renderers cannot initiate scans or enrichment themselves.
`notes.mjs` and `nicknames.mjs` retain independent revision fences and snapshot adoption.

The report order is overview, first action, devices, review items, the complete checklist
and supporting information. Device and review searches have independent state. All device
details start collapsed; an explicit Show more view reaches every result. All answering
features remain accessible inside their device. Failed/unstarted selected checks appear
as incomplete entries, not successful results or name-coverage denominators. Matched
announcements and comparisons stay with their device; technical evidence, original wording
and CVE research use contextual disclosures. Opening them does not request a lookup.

The saved network snapshot supplies scan-computer/gateway role labels without inventing
device names. The dashboard presents reported phases; single-device Deep checks use
activity rather than an invented percentage. Confident probed Windows/VMware names expose
reviewed, conditional feature help; port guesses do not. Light's saved ledger supplies
explicit scan-computer coverage. Every finding action is reachable in the complete
checklist; expansion and status filters never truncate the stored recommendations.

Optional enrichment saves a bounded earlier-device observation view when recent
Light discovery reports have matching scope, target and check selections. Only
previous completed device checks with unambiguous usable adapter addresses qualify.
An already-seen address suppresses an absence suggestion but does not establish
identity. The view excludes older unfinished checks and does not alter coverage,
findings or severity. It is not sent to Ollama. Existing reports are not backfilled.
Naming coverage separates current reported names, earlier saved names, unknown
sources, unnamed devices and user nicknames. Missing names are not security verdicts.
Comparison ordering and historical/cross-report name reuse share aware-UTC parsing
in `schemas/common.py`. Invalid or timezone-free times do not establish chronology;
one malformed previous report no longer invalidates other eligible candidates.
Compact summary ordering/pagination and library search now share the aware-UTC
policy. Search date filters use UTC days; readable reports with uncertain dates remain
accessible without date filters and with a warning. Recent device choices exclude
unknown/future/old dates and deduplicate by actual latest instant. A shared display
helper labels unusable times instead of guessing a timezone or rolling invalid days
forward. Saved dates/evidence are not rewritten.

Package verification provisions pinned build tools from `requirements-build.lock`
in an owned environment, then builds without backend dependency resolution and
tests the installed wheel separately with Python `-I`. Optional offline/wheelhouse
flags disable index access. This does not promise bit-for-bit builds or portable
cached binary dependencies across OS/Python versions.

No claim of multi-user production hardening, comprehensive vulnerability detection,
real-phone accessibility, reader-study completion or Ubuntu live verification is made.
The latest 12 October pair completed all six discovered Light checks and the selected
this-PC Deep check, enrichment and AI. Earlier dated reports retain incomplete
coverage, including the 8 October 23-of-24 Light result; those gaps were not rewritten.
The older baseline adapter timeout was reproduced before the query fix and did not
recur in the post-fix pair. Wider concurrency/long-duration Windows measurements remain
useful; the guard and old partial reports were not weakened or rewritten.
