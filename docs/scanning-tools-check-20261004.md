# Scanning tools and Windows self-scan check — 4 October 2026

Update: both findings below are now fixed. See [the fix and live verification
record](scanner-fixes-20261004.md). The original failed-test evidence is retained
below as history, not the current implementation status.

## Scope and verification

Reviewed Light/Deep command profiles, bounded process execution/cancellation,
report-state handling, storage/evidence and the existing module/template/asset
reachability checks. No source files were removed or reorganised unnecessarily.
Normal saved reports and the running normal backend were left untouched.

- App doctor: Python 3.14.2, Windows, Nmap 7.991 available, AI provider configured.
- Local `nmap --script-help` resolved all 11 distinct scripts used by the two
  profiles. This check did not probe network devices.
- Full isolated regression: **397 Python tests**, one real-provider test deselected,
  **no warnings**, **50 JavaScript tests**, Chromium/Firefox/WebKit, lint/format and
  nine module syntax checks. Artifact: `.test-artifacts/checks-b3162166c7/`.
- Light remains 12 TCP/three UDP ports; Deep all 65,535 TCP/25 UDP ports. No changes
  were made to either profile or to the network scope.

## Confirmed findings to address

### 1. Windows self-scan is incompatible with the forced physical adapter here

The user explicitly authorised Deep against this Windows computer. Local adapter
inspection identified `192.168.0.216` on the authorised home subnet. The test used
an isolated backend on port 8766 and separate JSON data.

Deep `5dbf183a-3f2c-4447-918e-303033186996` failed after two roughly two-second Nmap
attempts. Both exited zero but their XML reported zero hosts up, one host down and
no host element. The app retained `HOST_UNREACHABLE`; it did not claim clean results.
AI produced one validated overview. Refresh/history, four responsive widths and
both Deep Run again choices passed. The test-owned backend was stopped when idle.

A bounded diagnostic then compared the same local target with only TCP 8765 and
UDP 5353, using a ten-second host limit and zero retries:

| Nmap interface selection | Result |
| --- | --- |
| Forced current Wi-Fi adapter (`-e eth6`) | Zero hosts up, no service results |
| Automatic, without `-e` | One host up; TCP 8765 closed, UDP 5353 open-or-filtered |
| Forced adapter with ARP discovery disabled | Zero hosts up; could not determine destination MAC |

This isolates the observed failure to forced physical-interface selection for the
local host in this environment. It does not prove a general failure to scan other
devices. Recommended fix: detect exact local-interface targets and provide a narrow,
verified self-scan routing policy, preserving target authorisation/network continuity
and normal remote-device adapter binding. Add command/API regressions and repeat
the full self-scan. Do not disable binding globally or label this PC as asleep.

### 2. Already-cancelled runner still attempts process creation

A mocked `asyncio.create_subprocess_exec` confirmed that `run_process` attempts
process creation even when its cancellation event is already set on entry. The
mock blocked process creation; no executable or network probe was started by that
diagnostic. Higher-level queue checks reduce exposure, but the low-level boundary
should also reject pre-cancelled work. Recommended fix: return a cancelled result
before spawning and test that the subprocess factory is never called; also await
cleanup of the cancellation-watcher task. No new live cancellation failure was
observed in this check.

## Test-harness note and limits

The initial self-scan preflight stopped before any scan because the harness expected
a manually saved subnet. Settings correctly used automatic detection (`null`) and
the effective scope matched `192.168.0.0/24`. The harness now accepts automatic mode
only after checking the effective and detected authorised scope; app settings were
not changed. This was a harness assumption, not an application network-scope fault.

No new Light network sweep or Sony scan was run. The Sony remains in standby/off.
No home fingerprint was sent to NVD. The failed self-scan is not a full successful
Deep assessment. These observations and recommendations are recorded, not silently
treated as fixes or passes. Full live results are in the isolated test folder, not
normal report history: `.test-artifacts/local-deep-20261004-retry/`.
