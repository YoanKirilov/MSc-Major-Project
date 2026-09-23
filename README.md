# NetGuard AI (Network Assessor)

NetGuard AI is a local research prototype for assessing an authorised home network or a single lab device. It uses Nmap to record observed devices and services, applies fixed rules to produce findings, and presents the results in plain language. A local Ollama model can optionally select reviewed, simpler wording. Scans, settings, and explanations are saved as JSON files on this computer.

The report describes what the selected checks observed. A missing finding does not establish that a device or network is secure. Demo results are labelled separately and do not represent a real scan.

## What has been built

- A browser dashboard with **Light** and **Deep** scan choices, live progress, cancellation, and scanner status. The result page shows coverage, errors, observed devices and services, safe check output, prioritised findings, recommended steps, and technical details. Findings can be searched and filtered by severity.
- A bounded Light scan of **12 TCP and 3 UDP ports** across an authorised private IPv4 network. It discovers responding hosts, then checks selected services on those hosts.
- A Deep scan of **one explicitly entered host** inside the authorised network. It checks all TCP ports, 25 selected UDP ports, service versions, and a fixed list of safe Nmap scripts. It can take substantially longer than Light. Neither profile runs exploits, password guessing, or packet capture.
- Optional short mDNS discovery of local device announcements. Advertised names and services are shown as unverified observations, separately from confirmed open services and findings.
- Seven deterministic finding rules for selected services, with evidence, severity, limitations, and actions. Device type hints are conservative. Incomplete or failed checks remain visible in the report.
- Optional Ollama wording for finding titles, explanations, limitations, steps, and checks. The model chooses only from reviewed alternatives associated with the exact source text. Invalid output falls back to the fixed wording; the original guidance remains available.
- Actions on a saved report to **Refresh saved guidance** from recorded observations and **Simplify this saved report** with local AI. Neither action starts another network scan. Guidance refresh archives the previous guidance in the same JSON document.
- Local JSON storage with validated documents, per-scan locks, atomic writes, previous-version backups, and compact history summaries. The backend also supports labelled fictional demo data and saved demo runs.
- A loopback-only web server with a bootstrap session URL, an HTTP-only session cookie, and Origin and CSRF checks for changes. The configured scan scope is checked on the server.

## Requirements and installation

- Python **3.11 or newer**.
- Nmap for real scans. Install it separately and make it available on `PATH`, or set `APP_NMAP_PATH` to the executable. On Windows, a normal Nmap installation is detected in the usual Program Files location when possible. Run `doctor` below to verify it. Demo data and offline tests do not need Nmap.
- Ollama only if you want optional local AI wording. The app still provides fixed plain-language guidance without it.
- Node.js only to run the JavaScript tests.

From the project root in **Windows PowerShell**:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m app doctor
.\.venv\Scripts\python.exe -m app serve --port 8765
```

On **Linux/macOS**:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/python -m app doctor
.venv/bin/python -m app serve --port 8765
```

The server opens the application in your default browser after startup and prints an authenticated local URL in the terminal. Keep the server running while using the app. Use `--no-browser` if you prefer to open the printed URL yourself. `network-assessor doctor` and `network-assessor serve` are also available after installation.

The project does **not** automatically read `.env` files. Set environment variables in your shell before starting the server. `.env.example` is a list of example values, and `AI_ENABLED` in that older example is ignored; the AI on/off choice is saved on the Settings page.

### VS Code and Live Server on this Windows workspace

This workspace has a local VS Code task named **NetGuard: Start backend**. It starts `.venv\Scripts\python.exe -m app serve --port 8765` when the folder opens, if automatic tasks are allowed. You can also run it from **Terminal > Run Task**. The task opens the authenticated app after the server is ready.

Right-click `app/templates/dashboard.html` and choose **Open with Live Server** if you prefer that shortcut. The static preview redirects to the Python app at `http://127.0.0.1:8765/`; Live Server alone cannot run scans or read saved JSON. Refresh the browser after HTML/CSS/JavaScript edits, and restart the Python task after backend changes. If port 8765 is in use, stop the previous backend task before starting another.

The `.vscode` task and Live Server settings are ignored by Git, so they are **local to this workspace**. On another machine, use the terminal commands above or recreate the VS Code task.

## Using the application

1. Open the authenticated URL printed when the server starts. If the dashboard reports that Nmap is unavailable, install/configure Nmap and run `doctor` again.
2. Open **Settings** to review the allowed network, choose an interface if needed, and optionally enable raw XML retention, mDNS announcements, or local AI wording. The allowed network must be a canonical private IPv4 range of `/24` or smaller. If automatic network detection fails, configure the range explicitly. Only scan a network or device you own or are authorised to assess.
3. Choose **Light** to check the allowed local range, or **Deep** and enter one host inside that range. The dashboard shows progress from saved scan checkpoints. You can cancel a running scan.
4. Open the resulting report to review findings, device and service observations, coverage, and checks that did not complete. Use **Run again** only when you intend to start a new authorised scan.
5. For an older saved report, use **Refresh saved guidance** when offered. If Ollama is available and enabled, use **Simplify this saved report** to request optional wording without rescanning. The report keeps the original observations and guidance.

Each scan request must include an authorisation flag. The server restricts discovery to a configured RFC 1918 private IPv4 scope and requires a single in-scope host for Deep scans. A host that does not respond or a port outside the selected checks may still exist; the report makes this coverage limit visible.

### Optional local AI

Install Ollama separately, start it locally, and download the default model:

```powershell
ollama pull llama3.2:3b
```

The default provider is Ollama at `http://127.0.0.1:11434`. Enable **AI wording** in Settings after the model is available. The dashboard and Settings page report whether the model can be reached. `ollama launch codex` is unrelated to this application's AI integration.

The backend first saves the deterministic scan result. If AI is enabled, it sends an allow-listed version of the findings to the loopback Ollama API in the background. IP and MAC addresses, hostnames, device and service IDs, and raw scanner output are excluded. Responses are validated per field and saved in the scan JSON; AI cannot change severity, evidence, scan dates, or the stored rule-based actions. Requests are batched, prioritise higher severity findings, and are capped at 24 findings and 12 attempts per report. If the provider is unavailable or wording is rejected, fixed guidance is shown. AI wording is a readability aid, not a second vulnerability detector or a guarantee that every reader will understand the report.

## Configuration

The Settings page stores the allowed network, selected interface, raw XML retention, mDNS discovery, and AI choice in local JSON. These environment variables are read when the server starts:

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_DATA_DIR` | Location for local settings and results | OS user data directory for `network-assessor` |
| `APP_NMAP_PATH` | Explicit Nmap executable path, if auto-detection fails | Auto-detect |
| `APP_ALLOWED_NETWORK` | Server-side private IPv4 scan scope when no saved scope is set | Detect an active private network |
| `APP_MAX_CONCURRENT_SCANS` | Simultaneous real scan limit (1–8) | `2` |
| `APP_AI_PROVIDER` | Local AI provider | `ollama` |
| `APP_AI_BASE_URL` | Ollama HTTP endpoint; must be loopback | `http://127.0.0.1:11434` |
| `APP_AI_MODEL` | Installed Ollama model name | `llama3.2:3b` |
| `APP_AI_TIMEOUT_SECONDS` | Maximum provider request time (1–300 seconds) | `60` |

Use `python -m app doctor` to see the resolved data directory and whether Nmap can run. Use `python -m app serve --port <port>` to change the web port; the server accepts only `127.0.0.1` or `localhost` as its bind host. The VS Code Live Server shortcut is fixed to port 8765.

## Saved data and API

The app uses **local JSON only**; there is no SQLite database. By default, the data directory is outside this repository. Its main files are:

```text
<data-dir>/settings.json
<data-dir>/settings.previous.json              # after a settings update
<data-dir>/scans/<scan-id>/scan.json            # full result and explanations
<data-dir>/scans/<scan-id>/scan.previous.json   # previous revision, when available
<data-dir>/scans/<scan-id>/summary.json         # small history entry
<data-dir>/scans/<scan-id>/raw/*.xml            # only if raw retention is enabled
<data-dir>/demo-runs/<run-id>.json              # saved fictional demo run
```

`GET /api/scans` lists saved scan summaries, and `GET /api/scans/{scan_id}` returns a compact scan status. `GET /api/live-scans/{scan_id}` returns the full live report. `POST /api/live-scans` starts a scan, `DELETE /api/live-scans/{scan_id}` requests cancellation, and the two report actions use `/refresh-guidance` and `/explanations` under that scan URL. `GET /api/status` reports scanner, AI, mDNS, storage, and active-scan status. Settings use `GET` and `PATCH /api/settings`.

The demo API provides `GET /api/demo-findings`, `POST /api/demo-runs`, and `GET /api/demo-runs/{run_id}`. These use fictional findings and do not invoke Nmap. The current dashboard is scan-first; it does not have a demo button or a history page. Scan, settings, and demo-run changes require the local session and CSRF token.

Saved scan JSON can contain device addresses, hostnames, and optional raw Nmap XML. Review files before publishing them; the usual local preview data and `.env` files are ignored by Git, but a custom `APP_DATA_DIR` inside the repository may need its own ignore rule.

## Code layout

| Location | Responsibility |
| --- | --- |
| `app/main.py`, `app/cli.py`, `app/config.py` | Web app assembly, startup, environment configuration, and diagnostics |
| `app/api/`, `app/security/` | Routes, local sessions, CSRF checks, and scan scope validation |
| `app/scanner/`, `app/jobs/` | Nmap commands, process handling, XML parsing, mDNS, scan progress, and cancellation |
| `app/risk/`, `app/profiling/` | Deterministic findings, guidance refresh, and conservative device hints |
| `app/explanations/` | Ollama integration, reviewed wording, validation, and fallback |
| `app/storage/`, `app/schemas/` | JSON persistence and validated data models |
| `app/templates/`, `app/static/` | Dashboard, report, settings, styles, and browser scripts |
| `app/demo/` | Fictional demonstration data and saved demo runs |
| `tests/`, `docs/` | Automated checks, implementation decisions, and test history |

The live pages are `dashboard.html` (`/`), `scan.html` (`/scans/{scan_id}`), and `settings.html` (`/settings`). `base.html` is the shared settings layout. The browser scripts use `api.js` for authenticated requests and `report.mjs` for report wording. An older standalone `front end/` prototype was removed; it can be recovered from Git checkpoint `b9c3242` if needed.

## Testing and current limits

Install development dependencies with `python -m pip install -e ".[dev]"`. Run offline Python checks from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -m "not live_lab and not live_provider"
```

On Windows, if pytest cannot use its default temporary directory, pass a short, unique path inside the workspace with `--basetemp`. JavaScript checks require Node.js:

```powershell
node tests/report_ui.test.mjs
node tests/live_server_bridge.test.mjs
```

The last documented cleanup verification passed **118 offline Python tests** and **9 JavaScript tests**. The optional real Ollama check runs only when `RUN_LIVE_OLLAMA=1`; live lab checks require an explicitly authorised test network. See [testing notes](docs/testing.md) and [implementation decisions](docs/decisions.md) for the verification history and remaining work.

Current limits include selected-port coverage in Light mode, no packet sniffing, no credential or exploit checks, no scheduled scans, no browser history page, no independent vulnerability validation, and no completed nontechnical-user study. Deep mode broadens port coverage but still cannot prove that a device or network is secure. Live validation on the intended Ubuntu reference environment remains outstanding.
