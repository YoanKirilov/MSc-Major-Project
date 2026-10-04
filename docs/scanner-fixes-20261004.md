# Self-scan routing and cancellation fixes — 4 October 2026

Addresses the two confirmed findings in `scanning-tools-check-20261004.md`.

## Implemented boundaries

- `scanner/network.py:host_scan_interface` removes Nmap's forced interface only on
  Windows when the target exactly equals the local address in the verified network
  snapshot and the original interface matches that snapshot. Remote devices,
  non-Windows platforms and missing/mismatched context keep the supplied binding.
- Light/Deep host checks and optional NetBIOS checks use the same helper. Discovery,
  target authorisation, saved allowed subnet and the network-change guard retain
  their original adapter context. No global interface or scope setting is changed.
- Self-scan reports include a limitation note: locally reachable services may differ
  from services reachable by another network device. This is not a firewall exposure
  assessment from an independent machine.
- `scanner/runner.py` returns a cancelled result before process creation when the
  cancellation event is already set. Cleanup now awaits the cancellation watcher
  alongside the process/output tasks. Cancellation during execution is still handled.

## Verification

Focused tests cover six platform/context/target boundaries, both profiles for local
and remote targets with the guard still bound, non-mutation of the policy interface,
warning presence/absence, no subprocess call for pre-cancelled work and watcher
cleanup. Twenty-five focused tests passed.

Final verification including the report note passed **409 Python tests**, one
real-provider test deselected, **no warnings**, **50 JavaScript tests**, three browser
engines, lint/format and module syntax: `.test-artifacts/checks-b9a5917a68/`.
Installed package with the note passed six pages, ten assets, demo
read/create/reopen and dependency checks in `.test-artifacts/package-107e817e19/`.
Subsequent edits only split that note's source string for formatting; text is unchanged.

## Live verification

The user-authorised target is this Windows computer, freshly verified at
`192.168.0.216` on the home subnet. Deep job
`fcdc1ae4-186f-41fe-b8fd-fa72b6c83753` ran with the routing and cancellation fixes
in an isolated data folder on port 8766. Normal application history and its running
server are not changed. The live run began before the explanatory report-note
addition; that note is verified by regression tests, not claimed present in this
particular report.

The scan completed on its first attempt in **571.0 seconds**, with one checked
device, **14 open services**, **five review items** (one low, four informational),
no scan errors or warnings. XML replay matched all 21 stored service-state records
and five rule findings. All six AI records were accepted and independently
revalidated; the structured AI input contained no private device identifiers.

Refresh/history and 320/390/768/1440-pixel layouts passed without page errors.
Both Deep Run again choices passed without submitting extra scans. The isolated
backend was stopped after verification. The previously immediate zero-host failure
did not recur. These self-observations do not prove the same services are reachable
from another device. Restart the normal backend task when idle to load these changes.

Artifacts: `.test-artifacts/local-deep-fixed-20261004/`. No Sony scan, wider network
sweep or external CVE lookup is part of this verification.
