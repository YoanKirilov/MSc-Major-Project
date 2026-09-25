# Architecture and workspace review

Reviewed 25 September 2026. This is the current map; dated build snapshots under
`archive/` and older testing entries are historical, not the current implementation.

## Overall assessment

The design fits a local, single-user research prototype. Collection, deterministic
findings, AI wording, persistence and browser presentation are separate layers.
It is **not** a production multi-user service: do not expose it to the internet or
run several server workers against one data folder. No database migration is needed
for the current scope; JSON remains the storage format.

The latest Pi-hole setup extension is **implemented but untested**: deployment files are
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
| `app/templates/`, `static/` | Four pages, shared layout, CSS and six active JS modules |
| `app/demo/` | Fictional demonstration data; separate from real scan observations |
| `tests/`, `scripts/` | Automated checks, installed-package verification and cleanup tooling |

All five HTML templates, six JavaScript modules and the stylesheet are referenced by
active pages/imports. The asset-traversal integration test checks that every shipped
static file is reachable. All substantive Python modules are reachable from the app/CLI;
package initialisers are retained. No live source module was removed just because it
looked unfamiliar or had no direct HTML reference.

## Problems found and fixed in this review

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

Ollama selects reviewed plain-language alternatives; it is not an autonomous scanner or
a source of new vulnerability claims. IPs, MACs, hostnames and raw XML stay out of model
input. Severity and evidence remain rule-owned. Rejected wording has field-level reasons;
an unavailable model must not hide factual results. Validation tests and one real local
model check do not establish comprehension by nontechnical readers.

Pi-hole is an optional external name source, not a replacement scanning engine. DHCP and
network-history failures are isolated. Historical names require a matching observed MAC;
names alone never establish reachability or identity. Real instance verification is pending.

### Shared Light/Deep enrichment

`scanner/details.py` collects small structured `DeviceDetail` records after Nmap, before
Ollama. Both profiles use this path. mDNS discovery-mode observations are reused;
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

## Remaining limitations and recommended order

1. **External validation:** an explicitly authorised home-network device, actual Pi-hole,
   and the intended Ubuntu setup. No current-network scan is authorised or performed.
2. **Reader evaluation:** run the documented nontechnical-user study; retain evidence of
   what people understand, not only model/test success.
3. **Continuous checks:** add CI for the supported Windows/Linux Python versions. Local
   `scripts/check.py` is ready; a passing Windows run is not a Linux compatibility claim.
4. **Maintenance scale:** JSON checkpoints rewrite full documents. History uses caches but
   still enumerates report folders. Retention is preview-only; export/import, permanent
   deletion, incompatible-schema migration and a maintenance UI remain future features.
5. **Targeted refactoring:** the supervisor, explanation service and scan-page controller
   are the largest modules. Extract host execution, analysis scheduling and report rendering
   when extending those areas, under existing regression tests; a wholesale rewrite would
   not itself improve correctness.
6. **Dependency upkeep:** current tests emit pytest-asyncio/Python 3.14 and Starlette test
   client deprecation warnings. They are not runtime failures, but should be resolved before
   upgrading Python/framework versions. Keep runtime and development locks aligned.

## Data checked, not rewritten

The configured data folder contains 23 readable reports (13 completed, six partial,
three failed, one cancelled). The historical `.preview-data` contains 63 readable reports,
including old queued/running records; it is not the active job queue and was not reconciled.
Referenced guidance JSON is readable and device/report IDs match in both sets.
This checks storage consistency, not the truth of historical network observations.

See `testing.md` for exact verification and `storage-lifecycle.md` for recovery instructions.
