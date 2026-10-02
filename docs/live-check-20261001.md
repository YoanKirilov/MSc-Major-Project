# Live verification — 1 October 2026

## Scope and method

The owner authorised a Light scan after being told that the current LAN is
192.168.1.0/24, not the previously saved 192.168.0.0/24 range. The Deep device is
not yet identified; clarification was requested before making any Deep request.

Run the current application with real Nmap and loopback Ollama in isolated storage.
Use explicit scope/interface settings only in that instance: the current Wi-Fi
interface was verified through Nmap's local interface list. Retain raw evidence.
Do not modify normal settings/reports, weaken scope validation, or mock detection.
No Pi-hole installation or deployment is part of this test.

Artifacts: `.test-artifacts/live-light-20261001-a/` (private; do not publish raw data).

## Results

Light scan `ae4692c2-2597-4777-9799-ad3eec02d8b8` finished in **659.9 seconds (~11 minutes)**.

| Measurement | Result |
| --- | --- |
| Discovery | 29 candidate devices; 1 observed only through mDNS during discovery |
| Service checks | 28 finished; 1 unreachable after two attempts |
| Saved collection state | `partial`, honestly preserving incomplete coverage |
| Open services | 21 |
| Review items | 9: 1 medium, 4 low, 4 informational; no high |
| AI | 10 ready AI records in 2 requests; overview plus all 9 findings |
| Names | 20 preferred reverse-DNS names, 1 preferred mDNS name, 7 unnamed |
| Normal data | All normal JSON hashes unchanged |

The unreachable address was 192.168.1.168. Discovery observed it, but Nmap could not
reach it during two device-check attempts. Sleep/disconnection/filtering are possible,
not established causes. This is a coverage limitation, not a demonstrated app defect.
The medium item concerns locally reachable file sharing; it does not establish an
exploit, anonymous access or compromise. Open services are not automatically vulnerabilities.

Offline evidence replay matched all **420 service-state records** and all nine findings.
All ten AI records matched source-bound reviewed choices; rebuilt inputs contained no
observed IP/MAC/hostname or raw XML. Replay uses the application's parser/rules and is
internal consistency evidence, not independent security ground truth.

Browser verification passed refresh without duplicate submission (one scan POST),
history search/reopen, retained Deep-picker selection after refresh, and no horizontal
overflow at 320/390/768/1440 px. No browser script errors occurred. No new model download
or normal backend restart was required; the isolated instance shut down after checks.
The local-only Ollama service started for this run was left available.

The rendered report says "Scan finished; 1 device could not be checked", explains what
a service means, distinguishes review items from a break-in, and preserves the failed
check beside a retry option. Its first action concerns the highest-priority observation.
This is an editorial review, not proof of comprehension by nontechnical participants.

Deep scan pending identification of the requested device; no Deep scan started.
Reported TV-like names include `Room5TV.lan` at 192.168.1.159 and `TIZEN.lan` at
192.168.1.245. These are unverified name claims, not confirmation of the intended Sony.
The owner must select the target before the Deep request.

## Bugs and errors

1. **Confirmed Windows network-detection bug:** `detect_private_network()` expects an
   IPv4 default gateway immediately after its label in `ipconfig`. This connection
   prints an IPv6 gateway first and IPv4 on the following line. Detection returns
   `None` even though Nmap's interface/route list identifies the active Wi-Fi subnet.
2. **Saved-range override and unclear mDNS error:** normal settings retain the old
   /24, which takes precedence over detection. With no adapter on that range,
   mDNS reports "No single local interface matches the mDNS scan scope". That is
   a scope mismatch, not evidence that Nmap is absent. The explicit isolated scope
   successfully passed admission without changing the product code.
3. **Local AI startup delay, not a missing model:** Ollama was stopped at preflight.
   Started its installed service on loopback only (no model download). Health requests
   initially timed out while GPU discovery was running; after roughly 80 seconds,
   `/api/tags` responded with the configured `llama3.2:3b`. Final analysis completed
   successfully. The original preflight warning remains as historical evidence.

## Improvements

- Parse Windows routes/gateways robustly, including IPv6-first output, and cover it
  with regression tests. Do not silently choose a virtual adapter or a larger range.
- Distinguish Automatic versus Manual scope in Settings, and show which source is
  effective. A newly detected network should require confirmation of scan permission.
- Explain scope/interface mismatches using the saved versus current network, with a
  safe route back to Settings; distinguish zero matching interfaces from ambiguity
  or an unavailable interface-list command.
- Keep plain-language descriptions alongside technical service labels. Previous
  report review found labels such as `tcpwrapped` that still need beginner context.
- Distinguish an AI service that is stopped, starting, missing its model or failing
  requests. A starting message with bounded rechecks would be clearer than a generic
  unavailable indication; do not wait forever or hide saved scan facts.
- Explain that Light means limited scan coverage, not an instant result: this run took
  about 11 minutes for 29 candidates with two bounded host workers. Show measured progress
  and cautious timing guidance rather than promising a fixed duration. Any faster profile
  should explicitly state the coverage it omits; do not silently reduce checks.

These were findings/recommendations from the live run. The subsequent
[network recovery implementation](network-recovery-plan-20261001.md) addresses them:
parser correction, scope controls, scope-change rejection, mDNS diagnostics, AI readiness,
Light timing guidance and simpler technical labels. The owner's normal saved range was
corrected to the already authorised current /24 using the app's revision/backup API.
The original live run above still records the pre-fix code; it is not a new live test.
