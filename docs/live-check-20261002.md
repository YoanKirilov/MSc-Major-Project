# Home Light/Deep verification and cleanup — 2 October 2026

## Scope and settings

The owner requested both live profiles on the home network. Local preflight found
Wi-Fi on `192.168.0.0/24`, but the saved manual range was still `192.168.1.0/24`.
Updated only that range through the authenticated, revision-checked Settings API.
The preceding settings are backed up; mDNS, raw XML retention and required local AI
remain enabled. Pi-hole remains disabled and deferred. Nmap reported **7.991**;
Ollama reported **llama3.2:3b** available.

These runs use the normal backend and normal Saved reports, not synthetic scan
fixtures. Light selected the authorised /24. A fresh mDNS advertisement identified
the Sony KD-50X75WL at `192.168.0.239` before that single device was selected for Deep.

## Light result

- ID: `67ee98c5-248b-4a88-aa31-c58db6146a1c`.
- Report ready after 231 seconds: 13 discovered, 12 successfully checked,
  13 open services, 8 review items (4 low and 4 informational).
- One device, `192.168.0.226`, remained unreachable after two attempts. The cause
  was not established. This is incomplete coverage, not proof of a security problem.
- The headline correctly says **“Scan finished; 1 device could not be checked.”**
- All 180 service-state records and eight deterministic findings matched replay
  from retained Nmap XML.
- Ollama processed the overview and all eight findings in two batches. Seven
  records accepted alternative wording; two kept fixed wording with `not_simpler`.
  No fields were rejected. Rebuilt AI input contained no IPs, MACs, hostnames or XML.
- Sony's name was fresh mDNS evidence. The MacBook name was explicitly labelled
  as from a saved report; the computer name came from reverse DNS. Unnamed devices
  were not assigned invented identities. Two mDNS announcements were saved.

The real browser survived refresh without a duplicate submission, waited through
AI preparation, reopened the report from history and had no page errors. Report
reflow passed at widths 320, 390, 768 and 1440 pixels. These are browser viewport
checks, not physical-phone or assistive-technology testing.

## Deep interruption and repeat

The first Deep run, `318a814d-a504-49e4-aa48-9da714c3f628`, was interrupted by laptop
sleep. Windows Power-Troubleshooter recorded sleep at **20:33:37 UTC** and wake at
**20:52:04 UTC**. The job retried, then hit its overall 30-minute device-check limit.
It saved a failed report with `SCAN_TIME_LIMIT`, zero completed checks and a ready
AI explanation, rather than claiming the TV passed. Refresh, history reopening and
the four report widths also worked for that failed report.

This does not establish a fault in the TV. The report and raw interruption evidence
were preserved. A fresh Sony-only run was started after loading the small CVE UI fix.
The test runner makes a temporary, thread-scoped Windows keep-awake request and
releases it on exit; permanent power settings are not changed.

The fresh run **completed successfully**:

- ID: `c0cdbad1-e13d-478d-aa4b-53dd4bb1eb69`.
- About 11 minutes 20 seconds to the prepared report; one completed host attempt,
  15 open services (14 TCP and one UDP), and nine review items (two low, seven
  informational). No scan errors or warnings.
- All 32 explicit service records and nine findings matched retained-XML/rule replay.
  Bulk non-open TCP results remain in XML rather than thousands of JSON entries.
- All ten Ollama records, including the overview, accepted source-bound alternatives;
  no rejected fields or fallback records. The rebuilt model input was identifier-free.
- Fresh mDNS again supplied the Sony name. Only one service had a sufficiently precise
  application CPE for a CVE lookup; a detected product without a version was not enough.
- Refresh, history reopening and all four viewport widths passed, with no browser
  errors. The final browser review opened every finding on both usable reports and
  verified Deep Run again: Cancel, Same device prefill, and Choose another with an
  empty address. None of those setup choices submitted a scan.

Do not interpret Deep's additional services as newly opened ports: it checks a much
wider selection than Light. The sleep-interrupted report remains in history too.
All **42 earlier reports** and their **129 existing JSON files** were unchanged;
all **45 current reports** validated after the three deliberate scan submissions.
The backend was idle at final review and the temporary keep-awake request was released.

## CVE verification and a remaining matching gap

Real UI requests for the Light report's exact `lighttpd 1.4.67` and
`igor_sysoev:nginx:1.10.1` fingerprints both returned zero NVD records. Saved lookup
notes reopened correctly; the interface did not equate an empty result with safety.
With Deep active, CVE context correctly used fixed guidance instead of competing
for Ollama. This is a tested scheduling fallback, not an AI-generated explanation.
After Deep finished, retrying the cached router lookup produced an accepted real
Ollama explanation with no fallback reason. The response was a cache hit (no repeat
NVD query), saved notes reopened, and the mobile browser had no page errors.

A separate read-only public dictionary diagnostic found no exact dictionary entry
for the observed nginx identifier. Searching the same product/version showed a
deprecated `nginx:nginx:1.10.1` entry pointing to the current
`f5:nginx:1.10.1` entry. Therefore the current exact-CPE lookup can miss relevant
references when scanner and database naming differ. A separate diagnostic request
for that current identifier returned **15 records**, compared with zero for the
scanner's identifier. This establishes a reference-retrieval gap, not applicability
of those CVEs to the scanned device. No vendor was silently
substituted in saved scan evidence, and no CVE was asserted against the home device.

Recommended follow-up: add bounded product-dictionary resolution, preserve original
and resolved identifiers, follow explicit deprecation mappings, reject ambiguous
matches, and make unresolved identities distinct from a verified product search.
Never let a model invent the replacement identity. NVD documents deprecation
metadata in its [Product API](https://nvd.nist.gov/developers/products); its
[vulnerability API](https://nvd.nist.gov/developers/vulnerabilities) uses CPE criteria
for matching. The private diagnostic responses are retained with this test.

## Fix, organisation and regression

- Fixed an unnecessary CVE button for unversioned/OS/ambiguous fingerprints. The
  live report now supplies an eligibility flag computed by the same function as
  the lookup endpoint; the browser no longer duplicates an incomplete policy.
  This is presentation metadata, never a rewrite of the saved service evidence.
- Added a source-layout regression walking routed templates, inheritance and static
  imports, checking missing files and orphan assets. All application modules, five
  templates, nine JavaScript modules and the stylesheet remain in use.
- Archived 88 regenerated build/cache files before removing only `build` and
  `.ruff_cache`. Recovery ZIP:
  `.test-artifacts/cleanup-667f335d092e4a98b25dd46a7cf7a152.zip`.
  Saved data, virtual environments, historical evidence and source were preserved.
- Final lock-aligned check: **377 Python tests passed, one live-provider test
  deselected; 50 JavaScript tests passed; Chromium, Firefox and WebKit browser
  checks, Python lint/format and nine module syntax checks passed**.
  One existing Starlette/httpx deprecation warning remains.
- Installed-wheel check passed six pages, ten assets, demo read/create/reopen and
  dependency consistency. No home probes were made by the regression/package tests.

The earlier `.venv-brief` check also passed, but its older pytest-asyncio produced
Python 3.14 deprecation warnings. Final verification used `.venv-quality` with the
declared pytest/pytest-asyncio pins; no global dependency upgrade was made.

## Further improvements and limits

1. Resolve outdated CVE product identifiers conservatively, as described above.
2. Detect suspend/resume or interrupted connectivity during scans and explain the
   interruption specifically; offer a deliberate retry without treating silence as
   device safety. Consider an explicit optional keep-awake feature for long scans.
3. Continue nontechnical-reader testing. The report explains services, review
   priorities and failed checks accurately, but its device summaries plus technical
   table make mobile reports long. Consider collapsing technical detail by default.
4. Revisit the unreachable Light device when its owner confirms it is awake. This
   run does not identify why it stopped responding.

A passing software test suite is not proof of a secure network. Neither full device
name coverage, physical-device usability, Ubuntu execution nor the reader study is
claimed here. Private scan data, screenshots, model checks and test scripts remain
under `.test-artifacts/live-check-20261002/`; do not publish them automatically.
Final regression: `.test-artifacts/checks-e2e57a6589/`.
Installed wheel: `.test-artifacts/package-3fdfb07a8d/`.
