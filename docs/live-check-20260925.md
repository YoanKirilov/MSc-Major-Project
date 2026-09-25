# Home-network verification — 25 September 2026

The user confirmed being at home and requested live checks. The active default-route
network matched the saved home /24. Tests used new isolated data directories; existing
saved reports and normal app settings were not modified. No router/DNS settings changed.

## Live results

| Check | Result |
| --- | --- |
| Nmap / packet capture driver | Nmap 7.991 available; Npcap running |
| Local model | Ollama `llama3.2:3b` available |
| Light scan of this computer | Completed; one open service, no rule findings; AI ready |
| Home /24 Light discovery and service checks | 12 responding devices; all 12 device checks completed; no failures |
| Home observations | 180 selected port observations; 13 open services |
| Rule findings | 8 items: 4 low-priority HTTP observations and 4 informational service-review items |
| AI on home results | Overview and all 8 findings ready; 15 generated fields rejected and original guidance retained |
| Device naming | 3 devices had candidate names: 2 from mDNS and 1 from reverse DNS; one mDNS name had a conflict |
| Actual report in Edge | Counts, AI status, refresh, history reopen and Settings state passed; no page JavaScript errors |
| Real Pi-hole extraction | **Blocked: no configured URL/credentials and no responding local instance** |

The remaining 242 addresses did not become device service checks. A successful discovery
stage does not prove they contain no devices. The result is a completed **Light** scan,
not an exhaustive security assessment. No high/medium rule findings were produced;
this does not establish that the network is secure.

## Automated and installation checks

- Python suite including the real browser/synthetic scan test and real local Ollama test:
  **200 passed, 1 failed**. The host-concurrency test expected two simulated processes to
  overlap but observed one. It **passed on a focused rerun without code changes**. Its
  50 ms simulated-process delay makes overlap timing-sensitive; do not call the initial
  run entirely successful. Replace wall-clock overlap assumptions with synchronisation
  in a future fix.
- All **16 JavaScript tests** and six module syntax checks passed.
- Ruff lint and formatting checks passed for 76 Python files, using installed Ruff 0.16.8.
- Dependency consistency passed in the development and package-test environments.
- A fresh wheel built successfully with normal isolated build dependencies. Installing
  that wheel with `requirements.lock` into `.venv-package` succeeded, including Uvicorn
  0.54.0 and platformdirs 4.11.13. Four pages, seven assets and demo read/create/reopen
  passed. The normal `.venv` runtime was not upgraded; Ruff 0.16.9 was not installed.
- Initial sandboxed pytest attempts failed to access their temporary directories. The
  successful test execution used the approved unrestricted runner with isolated data.
  A preliminary `--no-isolation` wheel build lacked setuptools; the standard isolated
  build succeeded. Neither is evidence of a scan failure.
- Existing Starlette/httpx and pytest-asyncio/Python deprecation warnings remain.

## AI honesty and usability findings

The real overview accurately reported 12 device results, 13 open services and 8 items
to review. It explicitly said these observations do not prove a break-in and explained
what a service is. Saved findings retained their original severity and limitations.
For HTTP, the wording correctly said HTTPS redirection had not been checked.

The validation fallback worked, but the generated action/check lists frequently changed
length. Some other wording did not match reviewed alternatives. Original guidance was
retained instead of accepting those suggestions. The model integration is operational;
it is not successfully rewriting every requested field.

Follow-up improvements, not implemented during this diagnostic run:

1. Make the model's action-list output more reliable while retaining factual validation.
   Measure rejection counts against these real examples before changing model/prompt.
2. Replace visible field identifiers such as `recommended_steps` and `how_to_check` with
   everyday labels. Put detailed rejection counts/reasons in technical details.
3. Avoid duplicated coverage sentences, e.g. "12 device checks finished" followed by
   another sentence reporting the same count and zero failures.
4. Prefer a beginner-facing heading such as "This device offers a web page" over
   "HTTP service identified", retaining the protocol in technical details.
5. Address unknown/conflicting device names without guessing identity. Pi-hole can only
   contribute after a real instance with relevant records is configured.

These are a developer readability review, not a study with nontechnical participants.

## Pi-hole and outstanding scope

The app correctly displayed "Pi-hole is not configured" and disabled its enable control.
Pi-hole variables were absent from process/user/machine configuration. Docker was not
found on PATH or at its usual Windows installation path. The planned local API address
refused the connection. Offline Pi-hole connector/configuration tests passed, but those
use synthetic inputs and **do not verify extraction from a real Pi-hole**.

Next needs: an existing home Pi-hole v6 origin and a private application-password file,
or selection/setup of a suitable Pi-hole host. Do not publish the password in chat.
No Docker installation, VM creation, DHCP switch or router-wide DNS change was attempted.

A Deep scan remains pending selection of one authorised target device. Live failure/
cancellation/retry scenarios against a designated lab target, Ubuntu validation and the
nontechnical-reader study were not performed. Their automated synthetic tests are not
substitutes for those evaluations.

## Private local evidence

These ignored artifacts may contain home identifiers. Do not publish them unredacted.

- Automated run: `.test-artifacts/checks-4222b26c90/`
- Focused rerun: `.test-artifacts/worker-rerun-20260925a/`
- Single-computer scan: `.test-artifacts/live-home-v10cob1l/`
  Report ID: `6139bd20-e11d-4833-8c4a-47053455fa9f`.
- Network scan: `.test-artifacts/live-home-network-c6l56vjo/`
  Report ID: `97ddcace-aeba-4c22-9d31-ab999126588e`.
  Saved JSON/raw XML and `live-report.png` remain there. The screenshot was captured;
  the browser DOM was checked, but separate image inspection was denied by sandbox access.
- Wheel: `.test-artifacts/package-home-20260925/`

Both live test harnesses and the temporary browser server exited after completion.
Reports are separate from normal Saved reports. To view the home report later, stop the
normal backend and start it with `APP_DATA_DIR` pointing to the network test directory;
restore the normal data-directory setting afterward. Do not copy over existing reports.
