# NetGuard AI (Network Assessor)

NetGuard AI is a local research prototype for assessing an authorised home network or a single lab device. It uses Nmap to record observed devices and services, applies fixed rules to produce findings, and presents the results in plain language. Every new live scan saves its facts, runs local Ollama report preparation, validates and saves the wording, and then opens the report. Scans, settings, and explanations are saved as JSON files on this computer.

The report describes what the selected checks observed. A missing finding does not establish that a device or network is secure. Demo results are labelled separately and do not represent a real scan.

## What has been built

- A browser dashboard with **Light** and **Deep** scan choices, live progress, cancellation, and scanner status. The result page shows coverage, errors, observed devices and services, safe check output, prioritised findings, recommended steps, and technical details. Findings can be searched and filtered by severity.
- A bounded Light scan of **12 TCP and 3 UDP ports** across an authorised private IPv4 network. It discovers responding hosts, then checks selected services on those hosts.
- A Deep scan of **one explicitly entered host** inside the authorised network. It checks all TCP ports, 25 selected UDP ports, service versions, and a fixed list of safe Nmap scripts. It can take substantially longer than Light. Neither profile runs exploits, password guessing, or packet capture.
- Optional short mDNS discovery of local device announcements. Advertised names and services are shown as unverified observations, separately from confirmed open services and findings.
- Seven deterministic finding rules for selected services, with evidence, severity, limitations, and actions. Device type hints are conservative. Incomplete or failed checks remain visible in the report.
- Automatic Ollama preparation for the report overview and all findings, including reports with no findings or unsuccessful checks. The model selects reviewed alternatives tied to the saved facts. Original guidance remains available; an AI outage opens the factual report with an explicit retry message.
- Actions on a saved report to refresh guidance or retry AI preparation without rescanning. Unfinished host checks can be retried in a new scan limited to those devices. **Saved reports** reopens local history.
- Host checks receive at most two attempts, with separate timeout, scanner-error, invalid-output, output-limit and cancellation reasons. Light checks allow up to 180 seconds per host inside Nmap and 210 seconds per process; Deep limits remain 900/960 seconds. Two host workers share a global two-process limit, with a 30-minute host-stage budget; unfinished checks remain explicit.
- Device names combine Nmap discovery/service results, reverse DNS and optional mDNS, recording source, time and disagreements. Optional Pi-hole v6 integration adds names from address leases or matched historical records. A failed Pi-hole source does not discard names from another working source. A name does not establish reachability or device identity.
- Local JSON storage with validated documents, per-scan locks, atomic writes, previous-version backups, and compact history summaries. The backend also supports labelled fictional demo data and saved demo runs.
- A loopback-only web server with a bootstrap session URL, an HTTP-only session cookie, and Origin and CSRF checks for changes. The configured scan scope is checked on the server.

## Requirements and installation

- Python **3.11 or newer**.
- Nmap for real scans. Install it separately and make it available on `PATH`, or set `APP_NMAP_PATH` to the executable. On Windows, a normal Nmap installation is detected in the usual Program Files location when possible. Run `doctor` below to verify it. Demo data and offline tests do not need Nmap.
- Ollama and the configured local model for AI explanations. The app checks availability before scanning and attempts report preparation after collection. If Ollama remains unavailable, factual results stay accessible with a retry action.
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

The project does **not** automatically read `.env` files. Set environment variables in your shell before starting the server; `.env.example` lists supported settings. Legacy AI on/off values no longer gate automatic report preparation. For pinned installations, use `python -m pip install -r requirements.lock .`; development installs use `python -m pip install -r requirements-dev.lock -e ".[dev]"`.

Network detection uses the active default-route network, not an arbitrary virtual adapter.
If that network is larger than /24, select a smaller authorised range in Settings.
A mismatch with the saved range blocks scanning unless you explicitly select an interface
within that range. Being connected to a network does not grant permission to scan it.

### VS Code and Live Server on this Windows workspace

This workspace has a local VS Code task named **NetGuard: Start backend**. It starts `.venv\Scripts\python.exe -m app serve --port 8765` when the folder opens, if automatic tasks are allowed. You can also run it from **Terminal > Run Task**. The task opens the authenticated app after the server is ready.

Right-click `app/templates/dashboard.html` and choose **Open with Live Server** if you prefer that shortcut. The static preview redirects to the Python app at `http://127.0.0.1:8765/`; Live Server alone cannot run scans or read saved JSON. Refresh the browser after HTML/CSS/JavaScript edits, and restart the Python task after backend changes. If port 8765 is in use, stop the previous backend task before starting another.

The `.vscode` task and Live Server settings are ignored by Git, so they are **local to this workspace**. On another machine, use the terminal commands above or recreate the VS Code task.

## Using the application

1. Open the authenticated URL printed when the server starts. If the dashboard reports that Nmap is unavailable, install/configure Nmap and run `doctor` again.
2. Open **Settings** to review the allowed network, choose an interface if needed, check Ollama availability, and optionally enable raw XML retention, mDNS or Pi-hole names. An empty network field uses automatic detection. The allowed network must be a canonical private IPv4 range of `/24` or smaller. Only scan a network or device you own or are authorised to assess.
3. Choose **Light** to check the allowed local range, or **Deep** and enter one host inside that range. The dashboard shows progress from saved scan checkpoints. You can cancel a running scan.
4. Wait through **Making your results easier to understand.** The report then shows findings, observations, coverage and any unfinished checks. If simplification fails, use **Retry report preparation** after restoring Ollama. Saved scan evidence remains visible.
5. Use **Saved reports** to reopen previous results. **Run again** preserves the saved target; **Retry unfinished device checks** creates a new scan of only eligible unfinished hosts, revalidated against the current authorised range. Guidance refresh and AI preparation use saved evidence without rescanning.

Each scan request must include an authorisation flag. The server restricts discovery to a configured RFC 1918 private IPv4 scope and requires a single in-scope host for Deep scans. A host that does not respond or a port outside the selected checks may still exist; the report makes this coverage limit visible.

### Local AI report preparation

Install Ollama separately, start it locally, and download the default model:

```powershell
ollama pull llama3.2:3b
```

The default provider is Ollama at `http://127.0.0.1:11434`. The dashboard and Settings page report whether the model can be reached. `ollama launch codex` is unrelated to this application's AI integration.

The backend first saves factual scan results, then sends selected structured facts to the loopback Ollama API. IP and MAC addresses, hostnames, device/service IDs and raw scanner output are excluded. The report overview covers device and service counts, findings, coverage, failed checks and next steps. Each accepted sentence must match a reviewed alternative for its source; AI cannot change severity, evidence or rule-based actions.

Requests use batches of up to six items, prioritise higher-severity findings, and have at most two attempts per batch. There is no silent 24-finding cutoff. A 15-minute overall deadline includes waiting for the local model slot; individual calls have a 180-second ceiling in addition to the configured HTTP timeout. Accepted batches are saved and reused on retry. Failed preparation shows original guidance with a visible retry message, and accepted originals are not falsely labelled rewritten. Model, prompt version, input hash, output and failure reasons are stored. Readability still requires evaluation with nontechnical readers.

### Optional Pi-hole names

Run Pi-hole separately. Configure `APP_PIHOLE_URL` with its private IP origin and `APP_PIHOLE_PASSWORD` with a Pi-hole application password, restart the backend, then enable Pi-hole names in Settings. Prefer HTTPS with a trusted certificate; certificate validation stays enabled. The connector uses Pi-hole v6's documented local API, authenticates on the backend and logs out afterward. Credentials are not returned to the browser or saved with reports.

Only names inside the authorised range are used. Expired leases are ignored; historical IP associations require a matching MAC address. Imported names retain their source and time and cannot mark a device online. Router-only DNS forwarding, absent DHCP names and stale records limit coverage. No Pi-hole installation or router configuration is performed automatically. See [Pi-hole API documentation](https://docs.pi-hole.net/api/).

## Configuration

The Settings page stores the allowed network, selected interface, raw XML retention, mDNS discovery and Pi-hole choice in local JSON. These environment variables are read when the server starts:

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
| `APP_PIHOLE_URL` | Optional private IP origin of Pi-hole v6 | Unset |
| `APP_PIHOLE_PASSWORD` | Backend-only Pi-hole application password | Unset |

Use `python -m app doctor` to see the resolved data directory and whether Nmap can run. Use `python -m app serve --port <port>` to change the web port; the server accepts only `127.0.0.1` or `localhost` as its bind host. The VS Code Live Server shortcut is fixed to port 8765.

## Saved data and API

The app uses **local JSON only**; there is no SQLite database. By default, the data directory is outside this repository. Its main files are:

```text
<data-dir>/settings.json
<data-dir>/settings.previous.json              # after a settings update
<data-dir>/scans/<scan-id>/scan.json            # full result and explanations
<data-dir>/scans/<scan-id>/scan.previous.json   # previous revision, when available
<data-dir>/scans/<scan-id>/summary.json         # small history entry
<data-dir>/scans/<scan-id>/progress.json        # rebuildable polling cache
<data-dir>/scans/<scan-id>/terminal.json        # final status if primary hits size cap
<data-dir>/scans/<scan-id>/raw/*.xml            # only if raw retention is enabled
<data-dir>/scans/<scan-id>/guidance/*.json      # archived guidance snapshots
<data-dir>/demo-runs/<run-id>.json              # saved fictional demo run
```

`GET /api/scans` lists saved scan summaries, and `GET /api/scans/{scan_id}` returns a compact scan status. `GET /api/live-scans/{scan_id}` returns the full live report. `POST /api/live-scans` starts a scan, `DELETE /api/live-scans/{scan_id}` requests cancellation, and the two report actions use `/refresh-guidance` and `/explanations` under that scan URL. `GET /api/status` reports scanner, AI, mDNS, storage, and active-scan status. Settings use `GET` and `PATCH /api/settings`.

During scanning/analysis, the UI polls `GET /api/live-scans/{scan_id}/progress` instead of
repeatedly downloading full evidence. It opens the full report after processing finishes.

`POST /api/live-scans/{scan_id}/retry-hosts` starts a new scan limited to eligible unfinished hosts and requires the saved revision. Archived guidance is available from `/api/live-scans/{scan_id}/guidance/{name}`. The `/history` page reopens saved live reports.

Managed JSON reads and writes share a 20 MiB UTF-8 byte limit. An oversized write preserves the previous checkpoint and backup. At most three guidance snapshots stay inline; older snapshots, or snapshots that would exceed the document limit, move to separate JSON files with references in the report. Unusually large scan evidence can still hit the limit and is reported as incomplete rather than publishing an unreadable document. See [storage lifecycle planning](docs/storage-lifecycle.md).

Final status can be saved separately when the primary report is full, preventing endless
analysis polling. Offline `python -m app storage` commands provide an audit, retention
preview and explicit recovery into a new report ID; stop the backend first. See the
[safe recovery instructions](docs/storage-lifecycle.md). No automatic deletion is enabled.

The demo API provides `GET /api/demo-findings`, `POST /api/demo-runs`, and `GET /api/demo-runs/{run_id}`. These use fictional findings and do not invoke Nmap. Scan, settings, and demo-run changes require the local session and CSRF token.

Saved scan JSON can contain device addresses, hostnames, and optional raw Nmap XML. Review files before publishing them; the usual local preview data and `.env` files are ignored by Git, but a custom `APP_DATA_DIR` inside the repository may need its own ignore rule.

## Code layout

See the [current architecture review](docs/architecture.md) for responsibilities and
remaining limitations, and [workspace organisation](docs/workspace.md) for cleanup,
recoverable archives and the one-command check runner. Historical build notes and the
old UI screenshot live under `docs/archive/` and `docs/reference/`, not in runtime code.

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

The live pages are `dashboard.html` (`/`), `scan.html` (`/scans/{scan_id}`), `settings.html` (`/settings`) and `history.html` (`/history`). `base.html` is the shared settings/history layout. Templates and static files are explicitly included in the installable package. An older standalone prototype can be recovered from Git checkpoint `b9c3242` if needed.

## Testing and current limits

Install development dependencies with `python -m pip install -e ".[dev]"`. Run offline Python checks from the project root:

For all offline Python/JavaScript/lint checks together, run `python scripts/check.py`
or the VS Code **NetGuard: Check offline** task. Run artifacts stay in `.test-artifacts/`.

```powershell
.\.venv\Scripts\python.exe -m pytest -m "not live_lab and not live_provider and not browser"
```

On Windows, if pytest cannot use its default temporary directory, pass a short, unique path inside the workspace with `--basetemp`. JavaScript checks require Node.js:

```powershell
node tests/dashboard_ui.test.mjs
node tests/report_ui.test.mjs
node tests/live_server_bridge.test.mjs
```

See [testing notes](docs/testing.md) for current results and commands. The real Ollama test requires `RUN_LIVE_OLLAMA=1`; the browser workflow requires `RUN_BROWSER_TESTS=1` and uses synthetic scanner/provider responses. [Evaluation instructions](docs/evaluation.md) cover the remaining Ubuntu lab validation and nontechnical-reader study.

Current limits include selected-port coverage in Light mode, no packet sniffing, no credential or exploit checks, no scheduled scans, no independent vulnerability validation, and no completed nontechnical-user study. Deep mode broadens port coverage but still cannot prove that a device or network is secure. Live validation on the intended Ubuntu reference environment remains outstanding.
