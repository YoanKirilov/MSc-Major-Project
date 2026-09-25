# Architecture and workspace review

Reviewed 25 September 2026. This is the current map; dated build snapshots under
`archive/` and older testing entries are historical, not the current implementation.

## Overall assessment

The design fits a local, single-user research prototype. Collection, deterministic
findings, AI wording, persistence and browser presentation are separate layers.
It is **not** a production multi-user service: do not expose it to the internet or
run several server workers against one data folder. No database migration is needed
for the current scope; JSON remains the storage format.

```text
Browser templates + JavaScript
    -> authenticated API (session, CSRF, authorised scope)
    -> ScanSupervisor (bounded jobs, cancellation, retries)
         -> Nmap runner -> XML parser -> deterministic rules
         -> optional mDNS / Pi-hole naming -> conservative classification
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
| `app/scanner/` | Fixed Nmap commands, bounded subprocesses, safe XML and name sources |
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
