# Current architecture — remediation baseline, 3 October 2026

This is the current structural reference. Dated reports and the historical sections
of architecture.md are evidence logs, not current feature/test-count specifications.
See development-plan-20261003.md for implementation and verification status.

One loopback FastAPI backend owns one JSON data folder through an OS instance lock.
Authenticated/CSRF-protected routes validate bounded authorised private targets.
Light/Deep pages share the backend and nicknames; up to five jobs are admitted.

`jobs/supervisor.py` owns persisted lifecycle/checkpoints and cancellation;
`jobs/scheduling.py` supplies bounded queue waits and active execution budgets.
`jobs/transitions.py` contains pure failure, queue-expiry and restart report
transformations, separated from orchestration. Admission rejects an already-active
scan ID before replacing its task or cancellation tracking.
Discovery and host processes share two slots. AI has its own serial capacity and
separate queue/execution limits. Browser refresh observes the existing job, never
resubmits it. `jobs/enrichment.py` owns optional bounded device enrichment.

`scanner/network.py` reads structured Windows connections and Nmap adapter data;
new live jobs retain a network context and bind the validated adapter. A monitor
and pre-step checks stop work when the context changes or execution is suspended.
These are best-effort local checks, not an atomic network isolation mechanism.
On Windows, an exact self-target from this verified snapshot uses Nmap's automatic
local routing for host/NetBIOS checks. Discovery, remote targets and the network
guard retain the bound interface. A report note distinguishes self-observation
from what another device can reach. Pre-cancelled process work returns without
spawning; cancellation-watcher cleanup is awaited.
Linux context currently includes the selected adapter/address and default subnet;
the authorised Ubuntu lab still needs validation.

Nmap XML is parsed to typed observations; deterministic rules create findings.
Attempt metadata and optional per-attempt XML support diagnosis. mDNS adds unverified
advertisements and names, never proof of an open service. Already-discovered hosts
do not consume the eight-new-host advertisement allowance. Pi-hole is deferred.

Ollama receives selected, identifier-free facts and reviewed alternatives. Accepted
fields take precedence in the report; rejected, stale or unavailable model fields
use reviewed plain language. Original evidence and guidance remain accessible.

`scanner/cve.py` selects versioned, sufficiently confident application CPEs and queries
NVD only on request. `scanner/cpe_identity.py` consults its dictionary after an empty
lookup, rejects ambiguous/incomplete matches and retains resolution provenance.
A unique product/version under another vendor is explicitly a research candidate,
not an asserted identity. Public references are annotations, never scanner findings.
Full annotation snapshots prevent revision-only merges with stale editable fields.

JSON saves use bounded reads/writes, atomic replacement, revision checks and recovery
checkpoints. Offline export/restore uses checksummed new folders, never overwrites
existing evidence, and excludes session secrets. Retention is a preview, not deletion.

Templates and static modules remain reachable. No unused source files were removed.
The report keeps grouped next actions, device summaries and collapsed technical
details; eligible services expose CVE controls independently of findings.

No claim of multi-user production hardening, comprehensive vulnerability detection,
real-phone accessibility, reader-study completion or Ubuntu live verification is made.
