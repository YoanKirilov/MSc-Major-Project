# Live Light scan and report verification - 28 September 2026

## Scope and result

The active Wi-Fi matched the saved, previously authorised home network. Ran one Light
scan through the current app's authenticated API, real Nmap 7.991 and local Ollama
`llama3.2:3b`. Results are isolated from the normal app; recent report copies support
historical-name comparison. No Deep scan, Pi-hole request or router change was made.

Scan ID: `4098ba09-bfa5-4c8e-a293-c0f040b11159`.
Started 12:36:30 UTC; finished 12:40:05 UTC, including AI: **3 minutes 35 seconds**.

| Check | Observed result |
| --- | --- |
| Discovery | 10 devices |
| Host checks | 9 completed; 1 unreachable after two attempts |
| Services accepting requests | 11 |
| Review items | 7: three low-priority, four informational |
| High/medium findings | None; this does not prove the network is secure |
| Displayed names | Three: one current mDNS, one reverse DNS, one historical name |
| AI preparation | Eight records processed in two requests; zero rejected fields |
| AI changes versus retained originals | Six ready records; two accepted originals (`not_simpler`) |
| AI saved progress | 0/8, 6/8, 8/8; finished with no active items |

The unreachable host's retained XML explicitly reports zero hosts up and one down.
The new `HOST_UNREACHABLE` classification is correct; no evidence establishes whether
the device was asleep, disconnected or otherwise not responding. Its security remains
unassessed. The report headline correctly says **"Scan finished; 1 device could not be
checked."** No additional retry scan was launched.

Names were recorded from current sources where available; the TV's historical label
is visibly qualified as previously reported, not a fresh announcement. One optional
history comparison could not establish identity from an address alone. No collector
warnings were recorded, but this does not mean every possible device detail was found.
Pi-hole is not configured and was not tested.

## Verification

- Scanner, model and isolated storage passed preflight. No other saved scan was active.
- Opened the actual new report in headless Edge, every finding panel and device cards;
  checked desktop/mobile layouts and refresh. No JavaScript errors, HTTP failures or
  page-level overflow. Viewing did not change the saved report hash.
- All eight saved explanation records match approved wording choices. Original wording
  is retained in expandable details. Display-level plain-language choices are editorial,
  not automatically evidence that Ollama rewrote each displayed sentence.
- Replaying nine retained host outputs reproduced the service facts and all seven
  findings. The unsuccessful check remains separate from completed coverage.
- All **32 normal saved reports** validated read-only and were unchanged by these checks.
- The offline runner passed **304 Python tests and 24 JavaScript tests**, lint/format
  and seven JavaScript syntax checks. Existing dependency deprecations remain.
- No production code, normal configuration or running backend was changed. The first
  helper invocation stopped at an import error before scanning; running it from the
  project import context succeeded. Only one live scan was started.

## Readability assessment and remaining work

The new report explains a service as a contactable device feature, shows what was not
checked, asks users to identify devices before making changes, lists observed features,
and provides address-bar instructions with HTTP/password/certificate warnings. This is
a developer review, not evidence of comprehension by nontechnical participants.

Two improvements remain worth evaluating:

1. Shorten repeated explanations and keep the next action prominent, especially on
   mobile. The report is clearer but still contains substantial repeated qualification.
2. Make the reader-study conditions explicit. The normal page now prefers reviewed
   plain-language text even when Ollama keeps the original. Merely comparing normal
   pages before/after AI would not isolate AI's contribution. Use separately controlled
   wording conditions from identical synthetic facts and record retained-original cases;
   the session kit does not yet provide that comparison interface.

Controlled live Deep, actual Pi-hole, Ubuntu/remote CI and participant comprehension
remain unverified. A successful Light workflow is not a full security assessment.

## Private local artifacts

- `.test-artifacts/live-review-952sljxt/`: isolated report, retained XML, `review.json`,
  `evidence-audit.json`, desktop/mobile screenshots and device-card screenshot.
- `.test-artifacts/checks-9285fe3113/`: offline regression artifacts.

This report is in isolated test storage, **not** the normal app's Saved reports list.
Private raw evidence remains ignored by Git; do not publish it as study data.
