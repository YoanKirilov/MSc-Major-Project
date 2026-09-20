# Codex project instructions

## Goal

Build the MSc AI-assisted network vulnerability scanner as a local application, using this dashboard as the visual and interaction baseline.

## Architecture constraints

- Do not introduce a database.
- Persist scan configurations and results as local JSON files.
- Keep discovery/scanning, result normalisation, AI explanation, persistence, and UI presentation in separate modules.
- Treat every network target as explicitly authorised scope.
- Keep a demo mode using the included fictional findings until a real scanner result is deliberately connected.
- Never claim that a scan occurred when the interface is displaying sample or cached data.
- Validate JSON input before presenting it, and fail safely when a file is missing or malformed.
- Do not expose secrets, credentials, or sensitive host data in logs.

## Working approach

- Inspect existing files and the MSc build specification before changing architecture.
- Preserve working user code and make focused, reviewable edits.
- Create or confirm a Git checkpoint before large changes.
- Implement one end-to-end slice at a time and test it locally.
- Explain material design decisions and leave concise run instructions.
