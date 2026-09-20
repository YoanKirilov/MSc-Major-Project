# NetGuard AI — Local Dashboard Starter

This package contains the source files for the private dashboard prototype:

- `index.html` — page structure
- `styles.css` — responsive visual design
- `app.js` — interactive filters, search, sample findings, and remediation details
- `AGENTS.md` — project instructions for Codex

The current findings are realistic demonstration data. The prototype does not run a network scan and must not be presented as if it does.

## Place it in the MSc project

Extract this folder to:

```text
C:\Users\kiril\OneDrive\Documents\Masters\MSc Project\Code\dashboard-prototype
```

Open the parent `Code` folder in the Codex desktop app or in VS Code with the Codex extension. This lets Codex inspect both the dashboard and the rest of the MSc project.

## Preview the current prototype

From PowerShell:

```powershell
cd "C:\Users\kiril\OneDrive\Documents\Masters\MSc Project\Code\dashboard-prototype"
python -m http.server 8000
```

Then open `http://localhost:8000` in a browser.

## Suggested first Codex prompt

```text
Inspect the complete project before editing. Read Network_Security_Tool_AI_Build_Spec.md if it exists, then read dashboard-prototype/AGENTS.md and the dashboard source files. Integrate this dashboard into the local MSc network-security application. Keep the scanner engine and presentation layer separate. Replace the embedded sample findings through a small JSON data adapter, but preserve a clearly labelled demo-data mode. Do not add a database: results must be saved to and loaded from local JSON files. Create a Git checkpoint first, implement the smallest working vertical slice, run its tests, and start a local preview so I can verify it.
```

## Safe working practice

Before asking Codex to make substantial changes, initialise Git in the parent project folder and commit the current state. That gives you a clean checkpoint to compare or restore.
