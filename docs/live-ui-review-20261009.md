# Live scanning, architecture and plain-language review — 9 October 2026

Scope: review the completed UI changes, run authorised Light and this-PC Deep scans,
check saved evidence and displayed explanations, and recommend further changes.
No application-code fixes or dependency upgrades were made during this review.
Pi-hole remains deferred. No real NVD/CVE lookup was requested or performed.

## Authorisation and isolation

Windows detected Wi-Fi `192.168.0.0/24`, with this PC at `192.168.0.216`, rather
than the previous `192.168.1.0/24`. The user explicitly confirmed permission for
the new home range and this PC before either scan was submitted.

An owned, authenticated loopback backend on port 8766 used a fresh data directory:
`.test-artifacts/live-ui-review-20261009/data/`. The normal backend on 8765 was not
restarted or authenticated to. Existing normal report hashes remained unchanged.
Two historical reports from the previous range were copied unchanged into the test
directory; they are not a compatible same-network comparison baseline. This review
therefore does not measure naming or comparison behaviour with the user's complete
normal history/nickname library.

Exactly two network scans were submitted, one per profile. Test backends were stopped
after completion/review; a final listener check found the normal app on 8765 and no
listener on 8766. New test reports are in the isolated folder, not normal app history.

## Actual live results

| Measure | Light home-network scan | Deep this-PC scan |
| --- | --- | --- |
| Scan ID | `447c2157-bfff-4be1-a210-84f069b79ac3` | `fe71d984-bf39-4dab-bbc4-5f18379a23e5` |
| Final state | Completed | Completed |
| Selected/discovered device checks finished | 9 of 9 discovered | 1 of 1 selected |
| Open services/features | 12 | 13 |
| Review items | 8: four Low, four informational | 4 informational |
| Scan errors / unfinished device checks | 0 / 0 | 0 / 0 |
| AI records ready, including overview | 9 | 5 |
| Measured elapsed, including analysis | 339.6 s, approximately 5 min 40 s | 524.7 s, approximately 8 min 45 s |
| Retained service records replayed | 135, including non-open states | 20, including non-open states |

Runtime: Nmap **7.991**, Python **3.14.2**, local Ollama **llama3.2:3b**, prompt
**4.2.2**. Light checked 12 TCP and three UDP ports per discovered device. Deep
selected all 65,535 TCP ports and 25 UDP ports on this PC. Completion means the
selected checks finished, not that every possible security setting was assessed.

Deep retained the expected self-routing warning. A service answering a scan from
its own computer does not establish reachability from another device or the internet;
the report displays that limitation. Light retained two mDNS advertisements and one
reported name; the remaining eight usable device results had no current name. Missing
names are not evidence of intruders. The one Deep result had a reported name.

Four Light services had a sufficiently precise fingerprint/version to offer optional
CVE research; none of the Deep services did. These are eligibility counts, **not CVE
matches or confirmed vulnerabilities**. Pi-hole was disabled and not contacted.

## Verification completed

- Reparsed retained host XML and reran deterministic risk rules. All **155 service
  records and 12 findings matched** saved facts, excluding generated timestamps.
- Revalidated all **14 AI records** against their source-bound reviewed alternatives.
  No rejected fields or fallback reasons were recorded. Selected AI payloads contained
  no observed IP/MAC addresses, hostnames or raw XML. Ollama selected wording; it did
  not diagnose new vulnerabilities or generate new remediation instructions.
- Refresh recovery was exercised while both scans were running. Only the two original
  submissions occurred; the fixed Deep target remained visible and disabled.
- Reopened both completed reports on a fresh owned backend. The final browser pass used
  Chromium at 320/390/768/1440 pixels and Firefox/WebKit at 390/1440 pixels: **16
  engine/profile/viewport combinations**, no page errors and no horizontal page overflow.
  Startup at 390 pixels also rendered in all three engines. These are browser emulations,
  not physical-phone tests.
- Device disclosures and selected review items survived reload in all three engines.
  Chromium additionally checked device-search recovery, history reopening, Light Run
  again and Deep Same device setup. These setup actions submitted no additional scan.
- Captured and read the rendered detail text for all 12 review items, plus both report
  overviews. Mobile startup/detail screenshots were visually spot-checked. No automatic
  device-page opening, nickname edit, task-status edit or name lookup ran.
- Normal reports, copied historical reports and reopened live evidence hashes were
  unchanged. All **16 static assets** served exact current source bytes with `no-store`.
- Fresh `scripts/check.py` passed **582 Python tests and 102 JavaScript tests**,
  with 39 browser/provider/lab/study cases deselected. Ruff lint/format passed for
  143 files; all 15 JavaScript/module syntax checks passed. Artifacts:
  `.test-artifacts/checks-82dd9d9a88/`. The earlier complete synthetic three-engine
  gate remains separately recorded in [the UI execution record](ui-ux-followups-20261009.md).
- Static import traversal found all **67 application Python modules reachable** from
  app/CLI entry points. This does not prove every function is used or authorise deleting
  framework hooks, public helpers or test fixtures. No unused-file deletion was justified.

Final live browser evidence: `.test-artifacts/live-ui-review-20261009/browser-check-4191fff9/`.
Main scan reports, timelines, preflight and XML/AI replay evidence are in its parent.
Private logs can contain the local bootstrap URL; do not publish them or the live
device-identifying artifacts without sanitisation.

### Failed/intermediate checks, not counted as passes

The reused initial harness assumed the old device DOM and failed its selector after
both scans had completed. A first read-only viewer also wrongly expected the nickname
footer inside the disclosure; it is intentionally outside. Those assumptions were
corrected without changing app code. Another viewer assumed a full-IP search would
return one device and exposed the prefix-matching behaviour below. Its results were
recorded rather than hidden. The final viewer explicitly checks the current search
contract and persistence; it does **not** claim exact-IP matching is fixed. Earlier
artifacts and the final passing artifacts are retained separately. No scans were rerun
to correct browser-test assumptions.

## Bugs and follow-ups, in recommended order

1. **Storage-read error recovery — confirmed synthetic defect.** Injected `OSError`
   into `JsonStore.load_scan` and `load_progress` produced generic HTTP 500 responses
   from `/api/live-scans/{id}` and its progress route. The actual live reads succeeded,
   but a real transient I/O failure would give the user little recovery guidance.
   Introduce a consistent read-error boundary returning a bounded 503 response with
   instructions to reload/retry, preserving evidence and the pinned scan ID. Retain
   distinct missing/invalid-report and permission/lock handling. Add focused API and
   frontend regressions; never automatically submit a replacement scan.
2. **Exact-device search/identification — reproduced usability issue.** Searching
   `192.168.0.1` returned two device cards because general text search uses substring
   matching; it also matches `192.168.0.115`. That is consistent with the current code,
   but surprising for a complete address and can affect the recognition shortcut.
   Make a valid full IPv4 query exact for device identity, retain partial/text searching
   for other queries, and make the recognition action target one exact device. Test
   prefix collisions, empty/no-match states and saved-filter recovery without any
   scanner/name/CVE request.
3. **Windows socket-close diagnostic — reproduced runtime follow-up.** The final
   read-only browser session logged one `ConnectionResetError`, WinError 10054, from
   `_ProactorBasePipeTransport._call_connection_lost` during socket shutdown. All final
   browser checks and report reads passed. This is not a failed Nmap/AI result, but
   remains unresolved lifecycle noise. Investigate a small isolated close/refresh
   reproduction and supported runtime/server fixes; do not suppress unrelated errors
   or monkey-patch private transport methods. No version upgrade is claimed to fix it.

Diagnostics for the injected I/O failures and import traversal are in
`.test-artifacts/live-ui-review-20261009/offline-architecture.json`.

## Is the content understandable?

It is materially easier to follow: the overview defines a service as a device feature,
the report separates observations from safety claims, and review details use What we
found / What this means for you / What we could not confirm / What to do next.
HTTP items provide an actual starting address with permission, sign-in and certificate
precautions. VMware guidance explains where to look in installed applications without
telling the user to stop an ordinary service. AI-selected and editorial wording are
distinguished, with original guidance still available.

However, this was an assistant/editorial walkthrough, **not proof of comprehension
for everyone**. Remaining difficulties include:

- `TCP port`, `RTSP`, `HTTP`, `HTTPS`, software fingerprint and evidence-strength
  language still appear before their explanations. The glossary already exists, but
  is near the bottom of a long report.
- Generic R07 text says to check whether a connection is expected. A novice may not
  know how to answer that even when the feature label is meaningful.
- The compact first-action summary can recommend opening a device web page before
  the user reads the detailed no-password/certificate precautions. Keep that caution
  next to the summary action too, not only inside the selected review detail.
- Long feature headings repeat protocol/port information already in the location
  line. This consumes several lines on mobile before the explanation begins.

## Next UI improvements — proposed, not implemented

1. Apply exact-IP/recognition behaviour above, then add a guided identification path:
   recognise the device, compare the router's connected-device list, wake it if needed,
   optionally retry naming with permission, and save an explicit user nickname. Never
   invent a manufacturer/name or silently turn a name request into a scan.
2. Link unfamiliar terms to short explanations **where they first appear**, reusing
   the existing glossary. Prefer feature purpose in primary headings and keep exact
   protocols/ports in secondary technical context. Make help keyboard/touch accessible.
   This follows [W3C clear-word guidance](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o3p01-clear-words/).
3. Give generic-feature actions a cautious decision aid: recognise the device; decide
   whether the described feature is used; check its manual/settings or ask for help;
   do not disable it merely because it answered. Base examples on observed facts or
   clearly conditional reviewed guidance, not free-form invented AI advice.
4. Reduce mobile scrolling through an optional device-focused reading path and a
   visible count of that device's remaining review tasks. Keep the full report and
   original evidence reachable. Avoid repeating the same long feature title/address
   in every heading; preserve unambiguous association and uncertainty warnings.
5. Surface contextual first-action precautions and the self-scan limitation without
   requiring a supporting-details disclosure. Keep controls and task statuses clearly
   associated with the relevant device/action; marking Checked must never mean a
   verified fix. [GOV.UK task-list guidance](https://design-system.service.gov.uk/components/task-list/)
   is a useful structural reference, not a requirement to block this report until all
   tasks are marked complete.
6. Run the prepared nontechnical-reader protocol with consent and synthetic data,
   plus screen-reader/keyboard/real-phone/enlarged-text checks. Measure whether readers
   can state what was found, what remains unknown and a safe next step; do not use AI
   success or an automated readability score as a substitute. See
   [W3C user-evaluation guidance](https://www.w3.org/WAI/test-evaluate/involving-users/)
   and [the existing session kit](evaluation-session.md).

Live lab ground truth, Ubuntu, physical phones, screen-reader evaluation, participant
comprehension, Pi-hole compatibility and real CVE-provider behaviour remain unverified
by this review. A successful home scan and evidence replay do not prove vulnerability
detection accuracy or complete network inventory.
