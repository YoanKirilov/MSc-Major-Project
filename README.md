# Network Assessor

This is a local network assessment application built to the specification in the project brief.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
network-assessor doctor
network-assessor serve --port 8765
```

## Notes

### VS Code / Open with Live Server (Windows)

Open the project **Code** folder in VS Code. The workspace task **NetGuard: Start backend**
starts Python automatically when the folder opens. If VS Code asks, allow automatic tasks
for this trusted project. If no prompt appears, use **Tasks: Manage Automatic Tasks in Folder**
from the Command Palette, select **Allow Automatic Tasks**, and reopen the folder.
You can also start it immediately using **Terminal → Run Task → NetGuard: Start backend**.

The task opens the authenticated application in your default browser once the backend is ready.
Afterwards, right-click `app/templates/dashboard.html` and choose **Open with Live Server**;
the template forwards to the working app at `http://127.0.0.1:8765/`.
Live Server is an opening shortcut here; Python still handles scans, JSON results, and Ollama.
The browser uses the application's assets, so refresh it after editing HTML/CSS/JavaScript.
Restart the backend task after Python changes. **Tasks: Terminate Task** stops the backend;
stopping Live Server alone does not. If port 8765 is occupied by a previously started app,
stop that instance before starting the workspace task.

The `.vscode` setup is local to this workspace and is ignored by Git. On another machine,
copy these workspace settings/tasks or use the command-line startup above.

- The app stores all JSON data locally under the configured data directory.
- Scan updates use per-scan locks, unique atomic temporary files, and previous-revision backups.
- Demo mode works without a configured scanner or provider.
- Live lab and provider checks remain opt-in and are not run by default.

## Optional local AI explanations

The application can use a local Ollama model to select reviewed plain-language alternatives for
finding titles, explanations, limitations, and action wording. Each accepted sentence must match
an alternative bound to its exact source sentence; arbitrary model rewrites are rejected.
This preserves the meaning and avoids treating cosmetic edits as readability improvements.
The risk engine remains authoritative: AI cannot change
severities, evidence, or the stored recommended actions. Original rule-based wording remains
available in the report, and fixed guidance is shown whenever the model is disabled or unavailable.

Install Ollama separately, then download the default model:

```powershell
ollama pull llama3.2:3b
```

The application calls Ollama's local HTTP API directly. `ollama launch codex` is not required;
that command starts a separate Codex integration rather than the application's explanation service.

Choose the local model before starting the application:

```powershell
$env:APP_AI_PROVIDER = "ollama"
$env:APP_AI_MODEL = "llama3.2:3b"
network-assessor serve --port 8765
```

Then enable **AI explanations** on the Settings page. The saved setting is authoritative;
the old `AI_ENABLED` environment variable no longer overrides a user's choice. If AI is off,
the report still uses plain-English rule-based explanations. The dashboard shows whether AI
is enabled and whether the configured model is available. Existing scans are not silently
rewritten when this setting changes; open a saved result and choose **Simplify this saved report**
to request local AI wording without another network scan.
If the report offers **Refresh saved guidance**, use that first to update older rule wording
from the saved observations. It does not rescan devices or call AI. Previous guidance and AI
records are archived in the same JSON document, while evidence, severity, scan dates, and the
AI request count are preserved. Reports with insufficient saved evidence cannot be refreshed.
AI wording generated before the current validation version is hidden until requested again.
Local AI requests are batched, prioritise higher-severity findings, and stop after 24 findings
or 12 requests per report; the remaining findings keep their rule-based wording.

Optional mDNS device-announcement discovery can also be enabled in Settings. It uses a matching
local IPv4 interface for the authorised scope, runs briefly, and records advertised names and
services separately from Nmap-confirmed services and security findings. Raw packet captures are
not collected.

The server prints and opens a local URL containing the bootstrap token. API calls then use an
HTTP-only session cookie and CSRF token. The server intentionally refuses non-loopback binding.

After a scan, the backend loads its saved JSON document and sends an allow-listed version to
`http://127.0.0.1:11434`. IP addresses, MAC addresses, hostnames, device IDs, service IDs, and raw
scanner output are excluded. Structured output is validated and saved in the scan's
`explanations` records. The Ollama URL is restricted to the local loopback interface.
The deterministic result completes first; AI wording is generated as a background analysis and
falls back to fixed guidance when validation fails.
Validation is per line, so a rejected rewrite keeps the original line while reviewed alternatives
can still be used elsewhere. This is a constrained AI wording selector, not an independent
vulnerability detector or a guarantee that every reader will understand the report.

## Project layout

- `app/api/` — local web API routes and scan workflow.
- `app/scanner/` — bounded Nmap commands, process handling, and XML parsing.
- `app/risk/` — deterministic finding rules and guidance.
- `app/explanations/` — optional local AI rewriting with validation and fixed fallback.
- `app/templates/` and `app/static/` — the live dashboard and results interface.
- `app/demo/` — clearly labelled local demonstration findings.
- `tests/` — unit and integration checks.
- `docs/` — project decisions and verification notes.

The active pages are `dashboard.html` (start a scan), `scan.html` (results), and
`settings.html` (preferences), all in `app/templates/`. `base.html` is the shared
settings layout, not a separate page. Their scripts live in `app/static/js/`;
`api.js` handles session/API requests and `report.mjs` contains shared report wording.
`app/main.py` assembles the application; API handlers are in `app/api/`, including
the retained demonstration endpoints. Start the application with `python -m app serve`.

The unused standalone `front end/` prototype has been removed. Its original files remain
recoverable from Git checkpoint `b9c3242`. A local `.cleanup-backup-*.zip` also preserves
the source immediately before cleanup; backup archives are ignored by Git.

Local virtual environments, cache folders, temporary test output, and preview scan data are ignored by Git.
