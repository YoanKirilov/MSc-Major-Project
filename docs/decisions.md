# Implementation decisions

- The live UI has a single asset tree under `app/templates/` and `app/static/`. The obsolete standalone prototype is removed, while supported demo APIs and fixtures remain. Demo routes live in `app/api/demo.py`; shared route authentication lives in `app/api/dependencies.py`. The unused OpenAI SDK dependency is removed; Ollama continues to use the existing local HTTP client.

- Runtime persistence uses local UTF-8 JSON files only; no database or ORM is included. Per-scan file locks, unique atomic temporary files, revision checks, and previous-revision backups protect concurrent updates.
- The current development environment is Windows with Python 3.14.2. The specification's reference environment is Ubuntu with Python 3.12, so live Linux route and Nmap checks remain pending.
- Nmap and Ollama are optional at startup. Demo and offline explanation tests do not require either external prerequisite.
- AI is used only to simplify display wording for deterministic findings. Requests are restricted to a loopback Ollama endpoint, receive an allow-listed payload without network identifiers or raw output, and cannot replace stored rule-based severity, evidence, limitations, or actions. Original wording stays accessible in the report.
- The web server is loopback-only. A bootstrap URL creates an expiring HTTP-only session; state-changing API calls also require an Origin check and CSRF token. The allowed scan network is server-owned and cannot be widened by a request.
- Deterministic scan completion is independent from optional AI generation. Ollama work runs as a bounded background analysis and may safely fall back to fixed guidance.
- The saved AI setting is authoritative and defaults to off. Each live scan snapshots that choice; existing reports are not silently rewritten when the setting changes, but the user may explicitly request local rewording of a saved report without rerunning Nmap. Model wording is validated per line (title, explanation, limitation, step, check); invalid lines fall back to original wording. AI work is batched and capped at 24 priority findings per scan.
- Optional mDNS discovery is limited to the authorised local IPv4 interface and at most eight unique hosts. Advertisements are recorded separately as unverified observations; no passive packet capture is performed.
- History remains local JSON. Small per-scan summaries speed up listing, while the full JSON document remains authoritative. Automatic deletion, schema migration, and a human-understanding study remain future work.
