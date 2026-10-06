# Repeated Light and PC Deep check — 6 October 2026

Requested repeat after the successful earlier run. Before starting, Windows network
configuration again showed WiFi `192.168.0.216` with gateway `192.168.0.1`.
Light is authorised for `192.168.0.0/24`; Deep targets this Windows computer.
Nmap 7.991, Ollama `llama3.2:3b` and storage passed preflight.

The real UI submits the jobs to a separate backend on port 8766 with isolated JSON
and copied settings. Reports are saved in `.test-artifacts/repeat-live-20261006/`,
outside normal history. This verifies current source rather than the normal
instance's existing session. Pi-hole and external CVE requests are excluded.

## Results

Light `04135f30-b815-4f3d-bae2-53c83b7bfe1d` completed in 220.6 seconds: six
discovered devices, all six checked, ten open services and seven review items
(three low, four informational). No errors or warnings; all eight AI records were
ready. Refresh, history and widths 320/390/768/1440 px passed without page errors.
The previously observed addresses `192.168.0.53` and `192.168.0.65` were not observed
in this run. Their cause of absence was not established; this is not a host-check
failure or proof those devices no longer exist.

Fresh 390 px report load confirmed six collapsed cards, keyboard expansion and
section navigation. Active Deep progress used the updated wording and kept its
percentage on one line. This probe submitted no extra scan and had no page errors.

Deep `61860c89-7319-459d-918a-362ee076e8a7` completed on its first attempt in 550.9
seconds: one checked PC, 15 open services and four informational review items.
No scan errors. Its single limitation note explains self-scan routing and that
another device's view may differ. The earlier results are retained in
live-check-20261006.md.

Saved XML replay matched 90 Light / 22 Deep service-state records and all 7 / 4
findings. All 13 AI records revalidated, with zero rejected fields or fallback
records. The structured AI inputs contained no device IP, MAC, hostname or raw XML.
This establishes consistency with the evidence, not proof of reader comprehension.

Both profiles passed refresh, history reopening and four viewport widths without
page errors. Light Run again and both Deep choices returned to setup without
another scan submission. The test backend's stderr had no exception tracebacks;
it was stopped after all jobs finished. Normal app/history were left undisturbed
by the test workflow. The full offline suite was not rerun: no application code
changed in this live-verification pass.

No new application error was found. The previously recorded Windows reset remains
an unresolved intermittent runtime issue even though it did not recur. Four Light
software fingerprints were eligible for CVE research; no external lookup was made.
Deep returned no eligible application fingerprint. Pi-hole remains deferred.

| Observation | Earlier run | Repeat |
| --- | ---: | ---: |
| Light devices checked | 8 | 6 |
| Light open services / review items | 10 / 7 | 10 / 7 |
| Deep open services / review items | 15 / 4 | 15 / 4 |
| AI records validated | 13 | 13 |

Light obtained one current mDNS name in both runs; Deep obtained a reverse-DNS
name. The isolated folder contains no historical nicknames. Matching addresses
alone cannot establish unchanged device identity.

## Improvements to consider after verification

1. Show a visible step tracker and an activity indicator during single-device Deep
   checks. The completed-device percentage stays at zero for most of the run;
   elapsed time and check activity help, but a step sequence could explain the wait
   more clearly. Only show internal Nmap stages if captured reliably; show exact
   explanation counts during AI processing without inventing a time estimate.
2. Make recorded gateway/computer roles easier to read alongside actions, and make
   nickname assignment easy to find while identifying an unnamed device. Preserve
   each observed name and its source rather than replace it with a guessed identity.
3. Add a user-maintained action checklist, such as “I checked this” and “Ask someone
   for help”. Store it as separate editable notes with revision protection, retaining
   the scan evidence and severity. User acknowledgement cannot establish safety.
4. Make existing comparison information more prominent and explain count changes as
   “not observed in this scan”. Evidence is needed before attributing a change to
   sleep, disconnection, resolution or a different device using the address.

These are recommendations for later implementation, not changes made by this test.
