# Post-restart live verification — 7 October 2026

This is new evidence for the changes in `development-plan-20261007.md`, not a
relabelled copy of the earlier, pre-fix review. The requested repeat covered actual
Light and Windows-computer Deep scans, saved evidence, local AI, browser behaviour,
architecture and automated regressions. Application source was not changed in this
review; new faults and recommendations below remain for the next implementation.

## Scope and preservation

- Confirmed Wi-Fi `192.168.0.216/24`, gateway `192.168.0.1`, matching the previously
  authorised home range `192.168.0.0/24`. Virtual VMware adapters were not scan targets.
- Submitted exactly two live jobs through the browser: Light discovery of that home
  range and Deep on this Windows computer. No additional Deep scan of the Sony TV,
  exploit, credential attack or packet capture was run.
- Used an owned local instance on port 8766 with a fresh isolated JSON directory and
  copied prior test reports to exercise comparisons. The normal port-8765 session
  was not bypassed or stopped; these new scans are **not in its normal history**.
- Hash checks passed for every existing normal report and every copied report/XML
  file. Synthetic nickname responses intercepted the edit request in the browser:
  zero backend nickname writes. Normal nicknames/settings were not replaced.
- The test process stopped; a final listener check found only the normal port 8765,
  not 8766. The normal public pages and all eleven static assets matched current source.

## Actual scan results

| Check | Light | Deep: this Windows computer |
| --- | --- | --- |
| Saved scan ID | `aa5b79c1-7c89-4755-b9cb-00a7ad017385` | `2e7fb220-2f49-4e2f-a3b7-11131c3d12c0` |
| Observed wall time, including report preparation | 319.3 seconds | 545.5 seconds |
| Device checks completed | 9 of 9 discovered | 1 of 1 selected |
| Open/responding services | 12 | 14 |
| Review items | 8: four Low, four informational | 4 informational |
| Failed/unfinished checks | 0 | 0 |
| Scanner errors | 0 | 0 |
| mDNS announcements recorded | 4 | 0 |
| Validated AI records, including overview | 9 | 5 |

Nmap reported version **7.991**; actual report preparation used local
`llama3.2:3b`, prompt version **4.2.2**. Both finished in `completed`/`finished`,
with `analysis_status=ready`. Deep correctly retained the `SELF_SCAN_LOCAL_ROUTING`
note: a program answering on this computer does not prove that a different device
or someone on the internet can reach it. Light had no warnings. No backend exception
traceback or asyncio lifecycle diagnostic was recorded in the owned run; this does
not resolve the previously intermittent Windows reset.

### Names, comparisons and CVE boundaries

Light obtained **two current names from mDNS**, including the Sony device name;
seven device results had no detected name. None of those names came from Pi-hole,
which remained disabled. Deep obtained this computer's name from reverse DNS.
Advertisements are recorded as claims, not proof of identity or an open service.

The Light report exposed eight compatible service comparisons and one device that
could not be compared reliably. Its new earlier-observations view identified two
previously checked adapter observations, last at `.53` and `.65`, that were not
matched now. The separate section retains timestamps, the source-report link and
the explicit sleep/address-change/absence limitations; it does not add findings or
count absent devices as completed current checks. A different discovery count is
not, by itself, an app failure.

Four Light services met the current explicit application-CPE/version eligibility
rule; none of the Deep services did. No live NVD request was made in this repeat.
Port numbers alone were not treated as CVE evidence. Pi-hole installation/name import
and external vulnerability-provider availability are not certified by this run.

## Evidence and AI honesty

- Reparsed the saved XML into all **135 Light and 21 Deep service records**, including
  non-open states; replayed all **12 deterministic findings** without a discrepancy.
- Revalidated all **14 ready AI records** against the reviewed choices for their
  exact findings/overview. Zero rejected fields and zero fallback records.
- Rebuilt selected AI input and checked that observed IPs, adapter addresses,
  hostnames and raw Nmap XML were absent. These checks apply to this run's payloads.
- Model output did not create findings, assign new severity or convert unchecked
  coverage into a success. Stored reports were 175,299 and 25,738 bytes respectively,
  below the consistent 20 MiB managed-document boundary.
- The integration currently uses Ollama to **select reviewed plain-language
  alternatives**, not unrestricted diagnosis or autonomous CVE searches. This is a
  useful factual boundary, but missing explanations must be added to the reviewed
  wording/action catalogue; the model cannot invent a useful new instruction.

## Browser and regression checks

The actual browser run passed independent concurrent Light/Deep submissions,
refresh without a duplicate request, fixed Deep address and disabled setup controls,
visible mobile progress, report loading, exact-ID history search/reopening and
Run again. Deep's same-device choice returned to setup with the correct address;
neither Run again action automatically started a scan. Both live reports passed
320, 390, 768 and 1440-pixel widths without page-level horizontal overflow or page
errors. Progress was inspected visually as well as with assertions.

Fresh full gate passed **515 Python tests and 65 JavaScript tests**; one opt-in
provider-only test was deselected. Chromium, Firefox and WebKit covered the synthetic
workflow, active refresh and eight-viewport responsive matrix. Ruff lint/format
passed across 131 Python files, as did ten JavaScript module syntax checks.
The actual two scans exercised real Ollama separately from the synthetic gate.

Installed-package/security/disconnect gates from the preceding implementation were
not rerun here. Their earlier results remain separately dated evidence. Physical
phones, screen readers, Ubuntu and participant comprehension were not tested.

## Confirmed follow-up issues

### 1. Delayed nickname responses can regress the displayed saved version

In `app/static/js/scan.js`, `scheduleNicknameRefresh()` accepts any changed snapshot
without checking whether its revision is older than the already displayed one.
A browser-only diagnostic held an older poll response, completed a synthetic edit
and full report reload at revision 3, then released the revision-2 poll. Both the
visible device summary and in-memory revision regressed to the older label/version.
No server write reached storage and no original scan evidence changed.

The locked backend revision check still prevents a subsequent stale edit from
overwriting saved data, but users can see an outdated nickname and encounter an
avoidable conflict. This is a **confirmed frontend race**, not data corruption.

Next implementation:

1. Add a monotonic nickname snapshot-adoption boundary, including full-report reads
   after edits, and reject malformed/older replies before changing notices or labels.
2. Preserve readable scan evidence, focus, search and expanded device sections;
   coordinate in-flight poll/edit snapshots rather than starting extra writes.
3. On a stale-edit conflict, reload the latest nickname snapshot and explain that the
   edit was not saved. Do not silently retry a write with a new revision.
4. Add a delayed-poll/newer-edit regression and two-tab recovery tests, then repeat
   focused JavaScript/browser checks. Keep notes' existing monotonic guard intact.

### 2. Naming guidance refers to a button label that is not present

`presentation.mjs::namingCoverage()` tells readers to use a **Refresh name** button.
The report's actual button is **Try identifying this address again** in `scan.js`.
This does not break the lookup, but makes the instruction harder for a beginner
to follow. Align the wording and add a rendered-label regression; also reconcile
the glossary's "Unknown device" with the current "Unnamed device" label.

## Improvements recommended after those fixes

1. Give the common Windows/VMware review items specific, reviewed "what this is" and
   "where to check it" instructions. The friendly feature labels are useful, but
   generic advice to consult a device manual is weak for Windows program-to-program
   connections. Keep unknown identities explicit and do not advise disabling core
   Windows services or changing firewall rules without explaining consequences.
2. Explain when the scan computer itself was not discovered by Light. It was not
   among this run's nine Light results, although its separate Deep check succeeded.
   Existing silent-device limitations are honest; a specific local-computer coverage
   note would be clearer. Never add it to completed counts without an actual check.
3. Keep one concise first-action path on mobile, with advanced details collapsed.
   The layout fits, but repeated caution/checklist text makes a complete report long.
   Test reduction with nontechnical readers without removing evidence or limitations.
4. Consider extracting nickname snapshot handling and report sections from the
   roughly 1,000-line `scan.js` into tested small modules. Do not restructure solely
   to reduce a line count; preserve cached-import/version and rendering behaviour.
5. Finish the prepared reader study, physical-phone/accessibility and authorised
   Ubuntu evaluations. Retain Windows reset diagnostics and collect a real recurrence
   before deciding on a runtime fix. Keep Pi-hole as documented future work.

## Code organisation and evidence locations

All **66 application Python modules** are statically reachable from the entry points.
Candidate unreferenced names were manually checked: zeroconf/asyncio callbacks are
framework hooks, `storage_usage` is imported by the API and tests, and `NicknameStore.view`
has test/public-helper uses. No application file was safely proven redundant; none
was deleted. Static reachability is not a proof that every code path works.

- Live, replay, screenshots, browser checks and synthetic race evidence:
  `.test-artifacts/postfix-live-20261007/`.
- Fresh full regression: `.test-artifacts/checks-c84306ba4e/`.
- Authoritative race reproduction: `nickname-race-confirmed.json` records revision
  3 → 2 and the visible older label. Earlier diagnostics inspected a collapsed
  technical table rather than the visible summaries; one retry also incorrectly
  expected an enabled dashboard while it had recovered the active Deep job. Those
  exploratory checks are not presented as passes or app defects.
- `integrity.json`, `cleanup.json`, final listener inspection and the normal-frontend
  audit establish preservation/cleanup. No commit, app-source fix or source deletion
  was performed in this verification turn.
