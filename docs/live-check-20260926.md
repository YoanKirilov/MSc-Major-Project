# Live scan and beginner-readability review — 26 September 2026

## Follow-up after the beginner-report changes (20:59 UTC)

Ran a new authorised home Light scan using current code, Nmap 7.991 and local Ollama,
with isolated storage and copies of recent reports for historical-name comparison.
The normal backend and its saved reports were not changed. No Deep scan or Pi-hole
request was made. Pi-hole is not configured.

- Scan `1293a023-b11e-45c2-95e0-065144625d86`: 20:59:28–21:02:57 UTC (3m29s).
- Thirteen discovered targets: eleven completed device checks, two failed after two
  attempts. The report correctly says “Scan finished; 2 devices could not be checked.”
- Thirteen open services; eight review items (four low, four informational). No high
  or medium findings; this does not establish that the network is secure.
- Ollama prepared the overview and all eight findings in two requests: ready status,
  zero rejected fields. All displayed explanation fields matched approved choices.
  Validation success does not establish beginner comprehension.
- Three displayed names: one fresh mDNS TV name, one reverse-DNS name, and one
  historical MacBook name with its prior conflict disclosed. Not three fresh names.
- Desktop/mobile report, all finding panels and refresh passed without JavaScript
  errors, HTTP failures or page-level overflow. Viewing left the scan hash unchanged.
- Replayed eleven raw host results and reproduced all eight findings. All 27 normal
  saved reports remained readable and unchanged.
- Regression checks passed: 287 Python tests including synthetic browser workflow,
  then one separate real-Ollama synthetic test (288 total), 18 JavaScript tests,
  seven syntax checks, lint/format, and a fresh installed-wheel check (four pages,
  eight assets, demo create/read/reopen). Existing dependency deprecations remain.

Remaining findings, in suggested order:

1. **Classify zero-host results separately.** Two discovered targets returned no host
   record during service checking. Retained output for one explicitly reports a
   successful Nmap run with zero hosts up, not malformed XML. The parser's generic
   exactly-one-host requirement turns this into `HOST_RESULT_INVALID`. Keep coverage
   incomplete, but distinguish a device that could not be reached for checking from
   corrupt scan output. This evidence does not establish why the device stopped
   responding. Do not conceal the failure or turn it into a successful check.
2. **Prefer consistently plain language.** Three of four HTTP findings still display
   “HTTP service identified”; explanations retain terms such as “root page” and
   “redirect”. The model is selecting valid reviewed text, but sometimes chooses the
   technical original. Prefer the reviewed beginner alternative in the normal view,
   retaining technical wording in details; test readability separately from validity.
3. **Make actions directly usable.** “Open the device's web page” still assumes users
   know how. Explain how to recognise the device and where to enter its address;
   avoid encouraging credentials over HTTP or inferring a device's purpose. Device
   cards could list observed feature names beside their counts so users need not
   search the technical table to understand what was found.

No application fix was made during this checks-only follow-up. Remaining external
verification includes real Pi-hole, live Deep/lab scans, Ubuntu and participant study.

Private evidence: `.test-artifacts/live-review-cnxvbgno/` (`review.json`,
`evidence-audit.json`, saved report/XML and desktop/mobile screenshots).
Regression artifacts: `.test-artifacts/checks-ccc864fb04/`; separate provider test
under the live-review directory; fresh package `.test-artifacts/package-f9a644e542/`.

## Earlier baseline: scope and result

The active Wi-Fi matched the previously authorised home /24. Ran one Light discovery
scan through the current application's authenticated API and supervisor, in an isolated
data folder. Nmap 7.991 and local Ollama `llama3.2:3b` were used. Pi-hole was disabled
because no real instance is configured. No Deep scan, router change or packet capture
was performed; the normal running backend was not restarted or reconfigured.

Scan ID: `f122d075-1f4e-4d7a-b18e-14fdb74747dc`.
Started 12:47:15 UTC; finished, including AI, at 12:50:02 UTC (2 minutes 47 seconds).

| Observation | Result |
| --- | --- |
| Discovered devices / completed host checks | 10 / 10 |
| Failed host checks | 0 |
| Services accepting requests | 11 |
| Review items | 7: three low-priority, four informational |
| High / medium findings | 0 / 0; this is not proof of security |
| Current device names | 2: one mDNS, one reverse DNS |
| mDNS announcements | 2 from one device |
| AI | Overview and seven findings marked ready, two requests |
| Rejected AI fields | 16; original reviewed text retained |

The TV seen in an earlier report was not discovered in this scan; this run does not
show its name being removed. Two optional history details were marked not checked:
one lacked a recent matching device and another lacked a matching identity. These
are comparison limitations, not failed Nmap host checks. No collector warnings or
errors were recorded. The previously troublesome host completed this time; that does
not establish the cause of its earlier invalid result.

## Checks after the live scan

- Full runner: **276 Python tests** (274 offline, one real Edge synthetic workflow,
  one real local Ollama synthetic-facts test), **17 JavaScript tests**, six JS syntax
  checks, Ruff lint and formatting (83 Python files) passed.
- Fresh installed wheel with runtime lock pins: `pip check`, four pages, seven static
  assets and demo create/read/reopen passed on Windows/Python 3.14.
- Actual live report: loaded every finding panel in Edge, checked device cards and
  table counts, refreshed, captured desktop/mobile views. No JavaScript errors, HTTP
  failures or page-level horizontal overflow at 1440 px and 390 px. Viewing did not
  change the saved scan hash. This does not constitute a full accessibility audit.
- Replayed all ten retained Nmap host XML outputs: service facts matched the saved
  report, and the rule engine reproduced all seven findings. Only newly generated
  observation/creation timestamps were excluded from replay comparisons.
- Validated the overview and all seven displayed explanation records against their
  approved wording choices. Rejected suggestions were not substituted into the report.
- Read-only audit: **27 existing reports readable**, none changed; largest 170,330
  bytes, below the 20 MiB read/write boundary. States: 15 completed, eight partial,
  three failed and one cancelled. Historical failures are not new test failures.

Existing Starlette/httpx and pytest-asyncio/Python 3.14 deprecation warnings remain.
Ubuntu/remote CI, live Deep, real Pi-hole and participant comprehension are unverified.

## Problems to address, in recommended order

1. **Partial AI acceptance is cached as fully ready.** All seven finding explanations
   rejected their proposed action/check lists (14 fields); one meaning and one
   limitation were also rejected. Some other fields passed, so records became ready.
   A diagnostic on a disposable copy confirmed that another preparation request made
   **zero provider calls** and left all 16 rejected fields unchanged. Retry rejected
   fields explicitly, preserve accepted fields, and distinguish complete from partial
   wording coverage without hiding factual results. Keep factual validation strict.
   Code: `app/explanations/service.py` (`records_by_id`, pending selection,
   `_build_validated_record`); `app/static/js/scan.js` (preparation button).
2. **The red ring looks like a danger score, but is only a finding count.** It fills
   using `finding_count * 12`, regardless of severity. Here it showed seven findings
   with a prominent red ring despite zero high/medium items. Replace it with a neutral
   count and explicit priority breakdown; do not invent a security score.
3. **Internal validation terms leak into beginner explanations.** The actual screen
   showed `recommended_steps`, `how_to_check` and `limitations[0]`. Use ordinary labels
   such as “suggested actions” and “what we could not confirm”; keep rejection codes
   and field paths in expandable technical details.
4. **The first action is vague and the report repeats itself.** “Review the findings
   and their recommended steps” does not tell a novice where to begin. Device cards
   repeat long cautions, while the next-step list repeats the same HTTP action three
   times. Lead with identifying the affected device and one concrete check, group
   shared actions, and show the remaining detail on demand. Explain how to find a
   device's settings without automatically opening untrusted device URLs.
5. **Collection and explanation are not fully connected.** Optional redirect and
   device-detail observations are saved, but finding wording still tells the reader
   to look elsewhere for those checks. Add selected validated outcomes to the
   plain-language presentation, preserving the limited scope of each observation.
   Never send raw device text or identifiers to Ollama. Some rule guidance still says
   “open connection,” which can be confused with an active connection; prefer
   “feature accepting requests.”
6. **Unknown-device recognition is still difficult.** Eight of ten results lacked
   names. Do not manufacture labels or relax historical matching. Offer a clearly
   user-assigned nickname, explain where to find the router's client list, and keep
   source/time/confidence available. A missing name does not imply an intruder.

Beginner assessment: the overview and “not proof of a break-in” explanation are useful,
and the report does not claim these observations establish compromise or safety.
However, prominent red visuals, jargon, generic actions and repeated text still make
it harder than necessary to understand. This is an expert review from a beginner's
perspective, not evidence from an actual nontechnical-reader study.

## Private local evidence

All new scan data is under ignored `.test-artifacts/live-review-00dda88c/`, not the
normal saved-report history. It contains the scan JSON, retained raw XML, `review.json`,
`evidence-audit.json`, and desktop/mobile/card screenshots. These contain local network
identifiers; keep them private and sanitise before dissertation publication.

Suite artifacts: `.test-artifacts/checks-b7b39f5d9e/`.
Package artifacts: `.test-artifacts/package-d3daa7bec8/`.

No application code was changed during this review. Diagnostic helpers and this
verification record were added; previous workspace edits and saved reports were preserved.
