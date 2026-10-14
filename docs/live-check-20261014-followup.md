# Live verification after UI/UX fixes — 14 October 2026

See [implementation and offline verification](ui-ux-implementation-20261014.md).
This is the subsequent live pair, not the earlier successful pair on this date.

## Scope and isolation

Windows confirmed WiFi `192.168.0.216/24`, gateway `192.168.0.1`, matching the
authorised home scope `192.168.0.0/24`. Deep targeted this Windows PC only;
VMware/link-local networks were not scanned. Preflight: Nmap 7.991, local Ollama
`llama3.2:3b` available, mDNS enabled. Pi-hole was disabled; no Pi-hole or external
CVE request was made.

The actual runtime/browser used an owned backend and fresh private
`.test-artifacts/live-review-20261014-c/data`. Normal reports, nicknames and settings
were not edited. Historical names were not imported into this fresh folder.

## Results

| Result | Light | Deep — this PC |
| --- | --- | --- |
| Scan ID | `67740045-1c75-4b7a-ad51-328b55d4ff02` | `8b42330f-dc97-43d1-8597-3e06c24a21e4` |
| Final state / phase | partial / finished | completed / finished |
| Checks | 9 of 10 completed; 1 failed | 1 of 1 completed |
| Usable device results | 9; failed address shown separately | 1 |
| Open features | 10 | 14 |
| Review items | 7: 3 Low, 4 informational | 4 informational |
| Errors / warnings | 1 / 0 | 0 / 1: `SELF_SCAN_LOCAL_ROUTING` |
| AI records ready, including overview | 8 | 5 |
| Time including AI | 329.4 seconds | 529.3 seconds |

`192.168.0.72` was discovered, then Nmap could not reach it on either attempt
(about 2.4 and 2.1 seconds): `HOST_UNREACHABLE`. It might be asleep, disconnected
or refusing responses; the cause is unknown. This is a genuine failed check, not
evidence of a vulnerability or proof of an application bug. It was not hidden.

The actual Light heading is **“Scan finished; 1 device could not be checked.”**
Retry unfinished device checks is offered. Coverage says **“10 devices found during
discovery”**, not identified; remaining checks on the failed address are unassessed.
Deep labels **“This computer (scan source)”** and says an answering self-check does
not establish whether other devices/the internet can reach it.

## Evidence and UI verification

- Raw XML replay matched all 135 Light + 21 Deep saved service records and eleven
  deterministic findings. No completed-host raw evidence was missing.
- All thirteen accepted AI records passed reviewed-choice revalidation: zero
  rejected fields or fallbacks. Selected model input contained no recorded IP,
  MAC, hostname, scan range or raw XML.
- Chromium checked each actual report at 320, 390, 768 and 1440 CSS pixels:
  eight profile/viewport cases, no page errors/overflow. Saved text/screenshots
  were inspected for completion, uncertainty and wording provenance. This does
  not establish physical-phone or screen-reader usability.
- Exactly two scan submissions; refreshing both active pages retained their own
  jobs without resubmission. Report navigation waited for analysis to finish.
- All existing normal report files stayed byte-for-byte unchanged. The owned
  backend stopped and port 39043 no longer listened. Normal port 8765 was untouched.
- Private evidence: `browser-results.json`, `evidence-audit.json`, `integrity.json`,
  `cleanup.json`, timelines, raw XML, report JSON/text and screenshots in the
  artifact folder. Do not publish private artifacts without redaction/consent.

## Remaining issues and improvement work

1. Restart the normal backend after its jobs finish: it serves current assets but
   lacks recovery/capability routes. The UI now explains this and gracefully labels
   an old storage response instead of displaying NaN. The fresh backend passed.
2. One Light address remains unchecked. Wake/reconnect it and explicitly retry when
   authorised. Do not repeatedly rescan or claim its missing checks passed.
3. Names remain sparse: one Light mDNS name and a Deep reverse-DNS name. No historical
   nicknames were imported; this is not a proven regression. Existing bounded
   name-refresh/source diagnostics and router-list help remain available.
4. Actual AT speech, voice/switch input, physical phones, true browser zoom and novice
   comprehension remain pending: [prepared tasks](ui-components.md). Windows still
   blocks WebKit; no bypass/new WebKit pass is claimed.
5. Measure performance by stage before altering probes. Deep checking took about
   eight minutes, AI about 25 seconds. A one-device Deep check is not equal-work
   benchmarking against network Light discovery; never accelerate by hiding gaps.

No additional parser/rule/validated-AI corruption or UI runtime fault was found in
this bounded pair; this does not exclude every possible bug. No real report was
deleted. The post-live edit only handled an older backend's storage response; its
two synthetic browser cases and final installed-package tests passed separately.
