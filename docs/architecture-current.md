# Current architecture — updated 6 October 2026

This is the current structural reference. Dated reports and the historical sections
of architecture.md are evidence logs, not current feature/test-count specifications.
See development-plan-20261003.md for implementation and verification status.

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
Progress responses add live backend contact and scanner-process lifecycle activity;
these are not persisted completion estimates or proof of remote responsiveness.

`scanner/network.py` reads structured Windows connections and Nmap adapter data;
new live jobs retain a network context and bind the validated adapter. A monitor
and pre-step checks stop work when the context changes or execution is suspended.
Overlapping Windows adapter queries are shared across jobs/status calls; later
requests read afresh. Guards share overlapping checks and retain distinct failure
reasons for unavailable snapshots versus confirmed changes. Safety-triggered host
cancellation retains its cause. All failures still stop probing.
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
discovery addresses are excluded. Prompt version 4.2.2 invalidates older AI wording.

`scanner/cve.py` selects versioned, sufficiently confident application CPEs and queries
NVD only on request. `scanner/cpe_identity.py` consults its dictionary after an empty
lookup, rejects ambiguous/incomplete matches and retains resolution provenance.
A unique product/version under another vendor is explicitly a research candidate,
not an asserted identity. Public references are annotations, never scanner findings.
`static/js/notes.mjs` owns revision-aware, full-snapshot projection. It synchronises
titles, every checklist control, later name lookups, CVE panels and recovery notices
in place. Older delayed responses are rejected, even after a failed read; adoption
does not rebuild selected items, filters or expanded device cards. Lookup-button
focus is restored after temporary disablement. Notes I/O errors use readable 503
responses; unreadable/stale/invalid edits use 409 without resetting notes.

JSON saves use bounded reads/writes, atomic replacement, revision checks and recovery
checkpoints. Offline export/restore uses checksummed new folders, never overwrites
existing evidence, and excludes session secrets. Retention is a preview, not deletion.
Report annotations can recover a validated previous copy under the scan lock;
corrupt primary bytes are quarantined, revisions advance and the UI discloses
possible lost edits. Invalid backups do not silently reset notes. Quarantined
annotation files are included in offline exports.
Per-action user checklists live in `annotations.json`, keyed by saved finding/action
IDs. The authenticated, CSRF-protected update route requires a finished live report,
a valid saved action and the current annotation revision. To check is the default;
Checked and Need help are saved user notes, not verified fixes. Writes use the same
scan lock, bounded atomic replacement and previous-copy recovery as report titles;
they do not modify scan evidence, AI wording or severity. Stale-tab edits are rejected
and the latest notes reloaded rather than automatically overwritten.
Address-specific checklist labels distinguish unnamed or identically named devices.
Your review progress counts unique actions across the report; its status filter hides
controls, not observations or guidance. It is not scan coverage, a safety score or
proof of a repair. New reports do not inherit Checked.

Templates and static modules remain reachable. No unused source files were removed.
The report keeps grouped next actions, device summaries and collapsed technical
details; eligible services expose CVE controls independently of findings.
On mobile, device details start collapsed with coverage cautions still visible;
section navigation and native keyboard controls preserve access to detail. The
saved network snapshot supplies scan-computer/gateway role labels without inventing
device names. The dashboard presents the reported scan phases; single-device Deep
checks use activity rather than an invented completion percentage. Visible naming
toolbars stay grouped with their device even when details are collapsed. The overview
links to device identification, and a promoted comparison section summarises only
the existing conservative history evidence. See experience-plan-20261006.md for the
earlier implementation and verification. The current follow-up record is
`fixes-and-improvements-20261006.md`, including final live and offline results.

No claim of multi-user production hardening, comprehensive vulnerability detection,
real-phone accessibility, reader-study completion or Ubuntu live verification is made.
