# Improvements execution record - 18 October 2026

Scope: recommendations I1-I9 in [the audit](follow-up-audit-20261018.md).
Preserve the completed F1-F3 fixes, current page design, authoritative JSON,
revision/ownership controls, scan limits and truthful coverage. No new live scans,
automatic deletion, Pi-hole installation, database migration, commit or push.

Execution sequence:

1. I1/I2: select the actual browser engine in the remaining functional tests;
   separate common offline/package checks from browser jobs, retain all supported
   OS/Python/engine combinations, and save bounded redacted synthetic diagnostics.
2. I3: exercise current-shaped NVD edge cases, distinguish missing applicability
   from confirmed matches, and offer only validated user-opened advisory URLs.
3. I4/I5: make the first action easier to read without hiding safety limits; extend
   native keyboard/error checks and prepare explicit reader/assistive-technology
   evaluation. No invented participant or physical-device results.
4. I6: benchmark isolated synthetic JSON libraries below/above cache capacity,
   including concurrent reads/writes and cancellation. Only optimise measured work;
   keep data authoritative and cache rebuilding safe.
5. I7: extract narrow lookup/stage responsibilities and expose a public model
   preload interface. Preserve cancellation, queue limits and validation contracts.
6. I8/I9: explain unavailable JavaScript/custom-port startup and warn near recovery
   capacity, without adding automatic or permanent deletion.
7. Run the offline gate, selected Chromium/Firefox browser paths, installed package
   and saved-report checks. Record actual counts/artifacts, failures and limitations.

Human-reader studies, real assistive-technology/physical Safari checks, functioning
WebKit confirmation and a new hosted CI run require separate evaluation/environment
or publication. They will not be labelled complete from local synthetic tests.

## Implementation

| Item | Implemented now | Remaining evaluation |
| --- | --- | --- |
| I1 | CVE, library and workflow fixtures launch the selected engine; Chromium/Firefox exercised locally | Current hosted WebKit/OS/Python matrix and physical Safari |
| I2 | Four common offline/package jobs; twelve browser jobs; failure-only masked screenshots/redacted traces plus JUnit; bounded exports retained seven days | A newly published workflow run; no commit/push authorised |
| I3 | Current-shaped NVD fixtures, explicit unknown applicability, up to three validated NVD-tagged maker links; lookup policy bumped to `product-research-2` | Broader live public-database coverage and independent device/version verification |
| I4 | Short first instruction, separate visible precaution/limits and optional **Why start here?** explanation | Reader comprehension study, not inferred from shorter text |
| I5 | Keyboard/dialog/text-spacing/control-label tests and disabled-JavaScript recovery; expanded session tasks | Actual screen readers, voice/switch input, true zoom and physical phones |
| I6 | Isolated 32/600-report benchmark; measured hot-set cache improvement; byte-bound/revision/concurrency regressions | Representative rich-report, simultaneous scanner/inventory/search/cancellation load and long-duration measurements |
| I7 | Extracted explicit name operation and bounded analysis stage; public provider preload API | Further refactoring only where evidence justifies it |
| I8 | Home/report no-JavaScript guidance; report-module loading recovery; documented custom-port session URL | No automatic custom-port discovery was added |
| I9 | 80%-of-count/bytes recovery warning; private-backup guidance | Any permanent cleanup requires a separate explicit retention/deletion decision |

Scanner ports, scope checks, per-host retries, severity, evidence validation,
cancellation, queue bounds and original JSON remain unchanged. No advisory pages
are fetched, no AI-generated links are trusted, and missing applicability is not
treated as a clean security result. Maker links are NVD-tagged research, not proof
of maker identity or an affected device. Related references remain separately labelled.

The bounded cache admits the recent hot set instead of evicting it on every sweep
larger than capacity. Source/terminal fingerprints still invalidate it; names and
titles remain fresh separate reads. There is no database or persistent index, and
whole-library enumeration remains. Recovery warnings neither purge nor permanently
delete files. Existing Undo/Restore and fail-closed capacity limits remain intact.

The [evaluation session kit](evaluation-session.md#first-action-and-inclusive-evaluation---18-october-2026)
provides the next human tasks. No participant or assistive-technology outcomes have
been fabricated. The normal report remains a combined fixed/model-selected interface,
not a controlled demonstration of Ollama's independent effect on understanding.

## Local verification

- Offline gate: `.test-artifacts/checks-d40a97b669/` passed **938 Python**,
  five Windows link-privilege skips, 151 opt-in cases deselected, **270 JavaScript**,
  29 asset syntax checks, lint and 193-file formatting. An earlier complete run
  `.test-artifacts/checks-9ce7da8a05/` also passed. No live work was enabled.
- Focused Chromium/Firefox run `.test-artifacts/improve-browser-final-20261018/`:
  **28 passed; two new no-JavaScript test assertions failed**. Screenshots showed
  the warning visible; Playwright's text matcher skips the NOSCRIPT container.
  The corrected test checks the visible child paragraph, with explicit external/
  non-GET request guards. The final inclusive rerun
  `.test-artifacts/improve-inclusive-final-20261018/` passed **six cases** in actual
  Chromium/Firefox, including the two corrected cases and four rechecks. Across
  those executions, all **30 distinct focused cases** passed after correction;
  this is not a fresh clean combined full-suite/matrix execution.
  Earlier `.test-artifacts/improve-browser-20261018/` passed 28 cases before the
  additional no-JavaScript and maker-link assertions; it is not the final result.
- Installed wheel `.test-artifacts/package-fddb578f80/`: dependency consistency,
  seven pages, **31 static assets**, synthetic report/demo create/reopen/delete/Undo
  passed from outside the source tree. Pinned build/runtime tools came from the
  existing offline wheelhouse; no normal reports were deleted.
- Saved-only review
  `.test-artifacts/live-review-20261018-b/verification-5a18af049f/`: saved Light/Deep
  at 320/390/768/1440 pixels, exports, inventory filtering and return-focus passed.
  Zero scan submissions/page errors; normal reports and existing evidence hashes
  unchanged. The verification-owned backend stopped; the normal server was untouched.
- Workflow YAML parsed with the existing security environment: four offline and
  twelve engine combinations retained, browser jobs depend on offline, and upload
  paths are restricted to `.test-artifacts/ci-reports/`. CLI regressions check actual
  engine selection and exclude inherited live-provider opt-ins.
- Intentional failure probe
  `.test-artifacts/diagnostic-probe-final-run-20261018/` exited 1 **by design**.
  Its bounded export contained JUnit, a masked viewport screenshot and a valid
  redacted trace ZIP; known synthetic bootstrap/cookie/CSRF values were absent
  from the JUnit/trace contents. This is diagnostic verification, not an app failure
  or proof that arbitrary private data can safely be uploaded. Passing browser
  tests do not export screenshots/traces. Real/live-provider tests are excluded.
  The two unexpected assertion failures also produced useful bounded diagnostics
  (about 0.65 MB), which identified the visible no-JavaScript warning correctly.
- A read-only public NVD request for `CVE-2021-41773` returned HTTP 200 and the
  expected description/reference/configuration structure, including additive fields.
  Only a public CVE identifier was sent. This checks one current contract example,
  not every product mapping or a new scan/CVE enrichment of private reports.

### Cache measurements

Baseline `.test-artifacts/library-bench-57d9e8dbae/results.json` needed **600 full
JSON reads** for a repeat 600-report search. Final
`.test-artifacts/library-bench-d44173f7fa/results.json` needed **88**: roughly 85%
fewer full reads, with the 512-entry/8 MiB limits retained.

| Synthetic reports | Cold full reads / seconds | Warm full reads / seconds | Concurrent edit/search seconds | Control-task latency seconds |
| --- | --- | --- | --- | --- |
| 32 | 32 / 0.1243 | 0 / 0.0795 | 0.0911 | 0.0125 |
| 600 | 600 / 1.9916 | 88 / 1.5467 | 1.6244 | 0.0240 |

Every generated source `scan.json` hash remained unchanged; the synthetic title edit
was stored separately. These are small generated records and single timing samples
on a busy workstation, not a controlled speedup/SLA claim. Control-task latency
measures event-loop responsiveness while search is offloaded; it is **not** a live
Nmap cancellation measurement. Existing isolated supervisor/cancellation tests run
in the offline gate. Richer simultaneous-load measurements remain explicitly pending.

### Corrections and limits

Initial new check-runner regressions failed because their synthetic project omitted
the static directory. The test fixture was corrected; no application recovery or
validation was relaxed. A temporary test-file name collision was caught and the
unchanged original regression file restored; new cases use a separate filename.
Final gates include the preserved original regressions.

Security run `.test-artifacts/security-3d3d0ecf96/` found no known dependency
vulnerabilities and no medium/high static alerts, but failed on the deliberately
fake credentials in an unsafe-URL rejection test. Only that explicit synthetic
fixture line was allowlisted with its reason; no credential was printed, sent or
used, and no real-secret rule was disabled.

Final security gate `.test-artifacts/security-95aeb875a2/` passed: both pinned
dependency graphs had no known vulnerabilities; 16 low static alerts were retained,
zero medium/high alerts and zero potential secrets. Warnings about unhashed pins
remain visible; this pass is not proof that no security defect exists.

Local Windows WebKit remains blocked by OS code integrity; protections stay enabled.
No new hosted CI run, live scan, live model generation, real-phone/AT session or
participant study was performed. These changes remain uncommitted and unpublished.
Restart the backend when idle and reload tabs to load the backend/module changes.
