# Current architecture - updated 21 October 2026

The [21 October issue fixes](issue-fixes-20261021.md) close the four reproduced
edges from the [latest live review](live-review-20261021.md). Dashboard operations
and read finalizers are generation-owned; saved-start recovery precedes readiness.
Known Nmap interface failure reasons remain structured through snapshot/guard/report
storage, with bounded query time/output and no stale network authorisation. Report
coverage distinguishes interrupted, completed-empty and unrecorded discovery.
These fixes retain FastAPI, single-owner JSON, separate annotations and fail-closed
network checks. No fresh live scan was submitted; saved-report display/evidence
replay passed. The earlier Light interruption is preserved. Broader fresh-query
sharing/measurement, receipt maintenance and reader studies remain separate work.

The [20-21 October implementation](findings-implementation-20261020.md) resolves
the trust bootstrap, uncertain-start recovery and source-freshness findings from
the [preceding live review](live-review-20261020.md). Runtime/QA/security environments
now use pip 26.2.2 and standalone/vendored certifi 2026.10.19. Fresh CI/package
environments hash-verify pinned wheels before index access. No TLS or OS trust
protection is disabled; source identity and dependency audits remain separate checks.

`jobs/start_requests.py` reserves one durable scan UUID per explicit intention
before preflight. Browser starts and targeted retries pin their operation UUID in
the URL before POST; uncertainty/refresh uses authenticated GET recovery, not POST
replay or an arbitrary matching job. Changed settings/source report conflict, and
repeated accepted POSTs revalidate the current connection without starting work.
Legacy API clients without an operation ID remain supported and do not acquire
these deduplication guarantees automatically. The one-owner JSON architecture is
unchanged: short file-locked receipt writes, at most five preparing starts, 1 MiB/
1,024 receipts, no silent pruning. Corruption/capacity fails closed while saved
reports remain accessible. A future maintenance design must not discard receipts
in a way that lets an old intention run again.

API contract 3 protects dependent scan-start/retry and CVE writes from older
backends, retaining reads and cancellation. The normal server is still running
contract 2/build `3e5d3881e53f804e688b`; finish active work, restart its task, reopen
the session link and reload tabs. The verification helper now compares the actual
running source build as well as the contract; missing identity is unverified,
not a match. The updated installed wheel and saved-report reopening are verified
separately from deploying to the normal process.

The [post-review implementation](post-review-implementation-20261019.md) closes
the preceding review's reproduced retry/CVE/DNS edge cases. Targeted retry uses
the document's reason-qualified eligibility policy. CVE applicability is tri-state
and traversal-bounded. Private-address reverse DNS uses two bounded, cancellable
standard-library helpers instead of the default executor shared with JSON I/O.
Optional per-source diagnostics preserve uncertain naming outcomes.

Each service retains eight CVE completion receipts for cross-tab GET-only recovery,
separate from research dates. A process-frozen source build/API contract is exposed
in status/Settings and headers; source freshness is checked separately. Older
contracts block dependent CVE/start/retry writes, preserving evidence reads/cancellation.
Matching static assets alone still do not prove Python freshness. The helper's
same-contract/different-source comparison gap is now covered by regression tests.

The [I1-I9 improvements](improvements-20261018.md) retain the same scanner, scope,
JSON and admission contracts. `jobs/analysis.py` now owns the bounded analysis stage;
`static/js/name-lookup.mjs` owns explicit name-operation completion. Ollama runtime
uses the provider's public serialized `preload()` method instead of a private lock.
No scan, retry, port selection or AI evidence-validation policy is broadened.

Library search admits a stable recent hot set into the existing 512-entry/8 MiB
per-store cache, including byte-priority admission. Fingerprints still invalidate
changed scan/terminal files; editable labels are loaded separately. This reduces
measured full-file churn above capacity but does not eliminate whole-library work
or create a persistent index. Recovery capacity guidance warns at 80% without purge.

CVE policy `product-research-3` marks absent/unusable applicability as unknown and accepts at
most three validated HTTPS references tagged Vendor Advisory by NVD. These links
are user-opened research, not an authenticated maker identity or confirmed device
vulnerability. Ollama does not invent links; the app does not fetch advisory pages.
First-action instructions and precautions stay visible; optional reasoning moves
into a native disclosure. Source evidence and provenance remain available.

CI now separates four common offline/package combinations from twelve actual-engine
browser combinations. Only bounded redacted synthetic failure exports are uploaded;
real report folders and raw traces are excluded. This working-tree configuration
has not yet been published or verified by a new hosted run.

The [safe architecture/GitHub audit](safe-audit-20261016.md) provides a concise layer
map, confirmed limitations and prioritised open work. The local prototype retains
FastAPI, one owned JSON data folder, five admitted jobs/two scanner workers/one
analysis slot and evidence-validated local explanations. The
[18 October fixes](remaining-fixes-20261018.md) resolve the audited CVE timeout
mismatch and meta-only framing/MIME defences. Explicit CVE POSTs alone may wait
110 seconds; lost replies recover through saved-annotation reads without automatic
resubmission. Shared ASGI response headers enforce a self-only CSP and MIME/framing
protection, including error paths. Startup is external and CSP-compatible; unused
CDN-based interactive API docs are disabled while `/openapi.json` remains available.
[GitHub run 23](https://github.com/YoanKirilov/MSc-Major-Project/actions/runs/39079432854)
is now successful: all twelve platform/browser jobs and the security job passed,
including hosted Windows and Linux WebKit. Local Windows WebKit remains blocked
by OS code-integrity protection; that protection was not weakened. The
[18 October live review](live-review-20261018.md) records the authorised Light/this-PC
Deep checks and originally open issues. The follow-up reopens that evidence without
new scans or historical rewrites. Current results and verification limits belong to
those dated records, not older snapshots or an inferred new hosted CI pass.

The [Ollama/CVE follow-up](cve-and-ollama-followup-20261015.md) wires
`explanations/runtime.py` into the owned app lifespan. It maintains an installed
loopback-only server/model, with serialized health/startup, startup grace, cooldown
and bounded warm requests. It never downloads a model, alters OS startup or stops
another application's server. Source/fallback records remain factual even though
the repeated report outage notice and wording-retry control have been removed.
`service_product_cpe` enables separately labelled related-product research without
relaxing `service_cpe`'s version-specific policy. Saved CVE annotations have bounded
related fields and a lookup-policy version; legacy caches do not suppress the new
search. No scanner ports, scan scope, findings or risk severity are broadened.

The [edit-recovery follow-up](ui-ux-review2-20261015.md) adds a report-only conditional
native leave guard for dirty/pending label edits and unresolved checklist drafts.
It neither stores drafts nor automatically repeats writes. Explicit discard removes
protection immediately, before the native close event. Title success requires a
strictly newer matching server-normalised receipt; uncertainty keeps the draft and
refreshes saved notes. Hidden-character validation remains client guidance backed
by authoritative server checks. No scan, storage-schema or provider contract changes.

The [inclusive interface follow-up](inclusive-ui-implementation-20261015.md) changes
presentation only. `report-device-context.mjs` validates bounded explicit device
reading context, matched exactly against saved IDs without selector interpolation.
It never changes scope, authorises work or starts requests. Inventory links carry
that context; report reload/Back retain later reading state. Missing IDs do not
select a substitute device. Device cards foreground last recorded checks and review
needs; secondary history and original report facts remain reachable.

Settings and reports share `includes/display-controls.html`, including device-theme
selection. Saved display preferences remain local to the browser; OS motion is
automatic. Checklist feedback uses a designated final live outcome with static row
feedback. Native nickname-editor failures stay local; success is announced after
modal close. Inventory save outcomes use focused non-live feedback. These DOM
semantics still require actual assistive-technology evaluation. No scanner, rule,
AI validation, storage-schema or permission contract changed in this UI follow-up.

The [Settings simplification](periodic-removal-20261014.md) removes periodic
checking completely: no scheduler, monitoring API, runtime store or client module
is loaded. Only explicit user requests start scans. Existing `monitor.json` and
`monitor.previous.json` files remain inert and are included in private backups
for archival compatibility; startup never reads or executes them. Shared scan/AI
admission, capacity, deletion and restoration safeguards remain in place. Display
preferences retain theme/text size; motion follows the operating-system setting
and any legacy app-level motion choice is ignored.

The [third comparison round](competitive-round3-20261014.md) adds bounded 24-hour
per-tab inventory reading context in `device-library-context.mjs`. Only allowlisted
display context is stored; permission, credentials, labels and drafts are excluded.
Restore waits for the fetched list and does not override user interaction; reset
replaces prior context. `scanner/netbios.py` extracts one bounded endpoint-bound
computer name or an unavailable reason, not logged-in users/raw replies. Enrichment
1.0.3 shares it across profiles without changing probe/port/retry contracts. Earlier
certificate interpretation remains enabled. Historical records are not rewritten.

The [second comparison round](competitive-round2-20261014.md) adds allowlisted
whole-inventory device views applied before search/pagination, with an echoed view
contract. Unreadable household metadata fails label-based views explicitly; saved
facts remain available through All devices. The client preserves drafts on
unacknowledged or mismatched views/saves and requires a strictly newer matching
save receipt. `scanner/certificates.py` interprets complete bounded saved ssl-cert
date windows against service observation time. Enrichment version 1.0.2 applies to
both scan profiles without new probes, priorities or retrospective report rewrites.

The latest [device-first implementation](competitive-improvements-20261014.md)
adds an authenticated bounded `/api/devices` projection of saved live observations.
Unique adapter address plus authorised range groups records conservatively;
unmatched/ledger-only observations stay distinct. `device-labels.json` stores
revisioned household annotations separately, with locks, atomic backup and private
transfer coverage. Reports preserve structured bounded comparison deltas alongside
unchanged service evidence. Features view/shortcuts are presentation only.

`/api/live-scans/{id}/share` is a read-only privacy projection. Identifiers/notes
default off, redaction is bounded/fails closed, CSV escapes formula injection and
print media excludes the underlying identifying report. Both accepted final
wording and provenance are retained; original guidance remains technical evidence.

Deep's public profile is still `deep-tcp-v1`; recorded coverage ID now distinguishes
the SMB negotiation allowlist. `risk/smb.py` interprets only complete recognised
endpoint-bound script replies. R08/R09 describe SMBv1 support and optional signing
for the negotiated version, not proven exploits or Internet exposure. Ruleset
1.3.0 and prompt 4.4.0 keep reviewed plain-language validation and fallback.

The earlier opt-in periodic Light implementation has been removed, including its
routes, lifecycle hooks, storage models, browser module and scheduling-only
admission branch. Earlier execution logs describe that historical version, not
an available current feature. The shared admission lock still protects manual
parallel scans, standalone AI work, report deletion and restoration.

The execution record distinguishes final offline/browser/package/live evidence
from historical sections below and pending human/assistive-technology evaluation.

The [14 October implementation](ui-ux-implementation-20261014.md) adds keyed
running-job actions, explicit zoned dates/UTC filter days, durable Settings save
feedback and unsaved-state protection. The later [viewport/list fix](history-viewport-20261014.md)
restores per-tab History filter/page context into a complete fetched page; selection
is cleared. The old empty-start and one-gesture-per-row policy is superseded.
`history-context.mjs` owns bounded/expiring context and report identities;
`recovery.mjs` owns explicitly requested recovery listing/Restore. The existing
revision-safe archive machinery remains authoritative.

`GET /api/reports/recovery` is authenticated, bounded to 24 records per page and
inspects receipts/paths without following links. Restore rechecks revisions and
never overwrites. Managed recovery evidence/receipts are now included in offline
checksum backups; the bounded transfer limit is 3 GiB. Usage separates active and
recovery data. No purge is implemented. `GET /api/report-capabilities` exposes the
running Python feature contract so an older backend can show restart guidance.
Theme follows the device only when opted in; explicit Dark/Light still win.
See [the small component/state specification](ui-components.md) for shared rules
and the actual assistive-technology/reader tasks that remain pending.

The [report-management change](report-management-20261013.md) established bounded
pages and safe removal; its initial gesture-gated presentation is superseded.
`history-feed.mjs` loads the complete selected 24-summary page. `history-viewport.mjs`
uses IntersectionObserver solely for optional decoration: no hidden/inert rows,
missing-observer access dependency, artificial 100svh stage or scroll-driven data
growth. Focus cancels row animation. Pagination replaces the page and never advances
automatically. Filters apply across the library before pagination. Select this page
includes eligible offscreen rows of this page only; selection clears across pages
and filters. Removal still refreshes/corrects the current page safely.

Main navigation has Scan, My devices, Saved reports and Settings; display choices remain in
Settings without another global shortcut. Pi-hole UI bindings/control were removed.
Settings saves omit its legacy field, so they do not silently alter configuration
or erase historic observations. The optional backend implementation remains for
compatibility/documentation. No scanner or evidence contract changed in this fix.

Authenticated/CSRF report-removal and restore routes use bounded unique UUID batches
and per-item receipts. Supervisor admission serializes removal with scan/AI retries;
the per-report storage lock validates terminal state, scan/notes revisions and safe
paths before atomic directory rename into private `.trash/<trash-id>`. Undo validates
the stored receipt and never overwrites an existing report. Cancellation drains the
worker before admission is released. Global names/settings and scanner/provider
contracts remain unchanged. Recovery archives are bounded (1,000 entries/2 GiB),
not automatically purged and not immediate disk-space cleanup. Active/recovery size
accounting and managed recovery backup coverage were added on 14 October. Immediate
Undo receipts are held by the open page; the recovery browser works after that
UI action is lost. Verification limits
are recorded in the linked execution record.

The report-path guard uses `Path.is_junction` when available, or the Windows
mount-point reparse tag when it is absent. Its fallback branch is synthetically
tested on this Windows/Python 3.14 host, not claimed tested on actual Python 3.11
or Ubuntu. The latest offline gate passed 653 Python/190 JavaScript tests with
five actual Windows link-privilege skips; installed functional checks and the
96-file source/installed hash comparison passed. The final scoped Chromium/Firefox
history matrix passed 50 cases without assertion/cleanup failures; its earlier
harness errors are retained in the record. Six affected colour/settings/library/
synthetic-workflow regressions also passed. WebKit remains unverified under the
Windows startup block. Let active jobs finish before restarting the backend and
reloading the updated UI.

The [combined design polish](design-polish-20261013.md) adds truthful running/status
copy, accessible indeterminate task progress, inline Deep-input errors and spaced
job actions. Shared navigation exposes existing browser-local display preferences
in Settings without coupling them to server saves. Recent-device options are compact;
their separate descriptions retain saved evidence/date and manual target safeguards.
Its mirrored next-report controls are superseded by numbered report pages while
retaining zero initial requests and one-entry appearance. Conditional report recovery actions are grouped independently
of secondary tools. Scanner, provider, job and stored-evidence contracts are unchanged.

The [stable home-progress fix](home-progress-position-20261013.md) keeps progress
below setup on start/reconnect without automatic scrolling. Idle and running setup
share top-aligned layout. Pinned-job recovery and the scanning contracts are unchanged.

[The accessibility/reveal change](report-accessibility-20261013.md) supersedes
eight-entry history loading and paragraph alignment. History reset/open/search
now requests and renders no reports; intentional scrolling admits one entry at
a time, with gesture locking and an explicit keyboard alternative. Recorded
profile colours override visited-link colour and reverse on hover/focus.

`static/js/appearance.js` restores allowlisted theme and text-size choices from
bounded, versioned browser storage before the stylesheet. Native controls bind
on DOM readiness and update root datasets. Reduced motion follows the device
automatically; removed legacy motion choices are ignored without losing a saved
theme or text size. Display preferences are separate from scan facts and
per-report reading state; old alignment is ignored without losing searches or
disclosures. Light surfaces and severity/text colours are theme-aware. No scan,
job, provider or JSON-storage contract changes were needed.

The [home/history usability change](home-history-ux-20261012.md) consolidates the
home-page scan choices, target controls, readiness and primary action. Duplicate
Light/Deep navigation links are removed; their routes remain compatible and tabs
still observe separate jobs. `static/js/history-feed.mjs` now owns bounded 24-entry
pages, one-entry cached reveal, submitted-filter snapshots, stale-response rejection,
page-request retry and post-deletion page correction. The history controller reveals
on intentional downward scrolling, not repeated next-report buttons; it does not
chain requests on initial layout or after a response. Native list rows are scoped
to the selected page. Existing authenticated `/api/reports` whole-library matching
is unchanged; this is progressive rendering, not a new database/index.

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
