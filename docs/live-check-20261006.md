# Fresh Light and PC Deep verification — 6 October 2026

User requested fresh scans after restarting the task. The previous attempt was
rejected by the automatic approval review because of a usage limit and started no
jobs. Today, the local Windows network query confirmed WiFi `192.168.0.216`,
gateway `192.168.0.1`, and home range `192.168.0.0/24`. The normal app was reachable.

Tests use a fresh backend on port 8766 with isolated JSON storage and copied
settings. This verifies current source and the home network; it does not certify
the running normal instance or place these reports in normal history. Artifacts:
`.test-artifacts/restart-live-20261006/`. No Pi-hole or external CVE lookup is used.

Nmap 7.991 and local Ollama `llama3.2:3b` were available before launch. Light uses
the verified home range; Deep targets this Windows computer at `192.168.0.216`.

## Results

Light `450782d6-fce9-46bc-8f8e-d616fc5ed988` completed in 220.9 seconds:
eight discovered and checked devices, ten open services, seven review items
(three low, four informational), no scan errors or warnings. All eight AI records
were ready before the report opened. Refresh, history reopen and widths
320/390/768/1440 px passed without page errors.

Fresh mobile verification at 390 px confirmed eight initially collapsed device
cards, keyboard expansion and section navigation. Deep's live percentage remained
on one line; the waiting message contained the updated plain language and live
activity. No extra scan was submitted. Light's first suggested action displayed
the saved gateway role without inventing a device name.

Deep `70ccfffc-57ad-46bc-ab29-2b066f9baff1` completed on its first attempt in
551.4 seconds: one checked device, 15 open services and four informational review
items. No scan errors were recorded. Its one limitation note explains that checking
the scan computer locally does not establish what another device can reach.

Saved XML replay matched all 120 Light / 22 Deep service-state records and 7 / 4
findings. All 13 AI records (eight Light, five Deep) revalidated, with zero rejected
fields or fallback records. Selected AI inputs contained no device IP, MAC,
hostname or raw XML. Both reports passed refresh, saved-history reopen and all
four viewport widths without page errors. Light Run again and both Deep choices
returned to setup without another scan submission.

The backend log contained no exception tracebacks. The previous Windows reset did
not recur, which does not establish that its underlying cause is repaired. The
owned test backend was stopped after all jobs finished; normal app/data were not
used for scan writes and were left running as found. The local test artifacts
retain both reports, timelines, XML, screenshots and the evidence audit.

## Remaining observations and recommendations

- Current names depend on available responses: Light obtained one mDNS name, while
  the TV address did not return a current name. Deep obtained a reverse-DNS name.
  The isolated folder has no historical identity/nickname data; do not compare its
  naming count directly with the populated normal app history.
- The gateway/scan-computer roles now accompany suggested actions. A next usability
  refinement could explain “network gateway” as the device providing the route to
  the internet, retaining its saved source and identity uncertainty.
- Deep's device-completion percentage remains 0% until its sole host check ends.
  The new running-check and elapsed-time messages clarify this; stage-based progress
  could communicate the wait more clearly without inventing a precise estimate.
- Four Light software fingerprints were eligible for CVE research, but no external
  lookup was performed. Deep had no eligible application fingerprint; that does
  not establish an absence of vulnerabilities. Pi-hole remains deferred.
- A real nontechnical-reader study and a supported Windows runtime fix remain
  evaluation/dependency follow-ups. Neither scan exposed a new application failure.

## Reading the results

The report defines a service as a device feature others can contact and identifies
review items as observations to check. Coverage and limitations remain visible.
No findings or a completed scan is treated as a security certificate. This is an
evidence/wording review, not a study with nontechnical participants.
