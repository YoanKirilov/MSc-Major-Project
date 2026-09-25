# Implementation decisions

- September 25 audit: default-route network selection must not fall back to virtual
  adapters. Saved-scope mismatches require an explicit matching interface before scanning.
- Progress is a small authenticated endpoint backed by a rebuildable cache. Host checks
  use two workers across all jobs and a 30-minute stage limit; unfinished checks stay visible.
- A revision-bound terminal sidecar prevents a full report from remaining stuck in analysis.
  Maintenance recovery creates a separate report; audit and retention preview never delete data.
- Prompt 4.2.0 adds field-level rejection reasons. Pi-hole source failures are independent,
  discovery identity is preserved, and classification is refreshed after enrichment.
- Real network validation is deferred until the user is at home on an authorised network.

- The live UI has a single asset tree under `app/templates/` and `app/static/`. The obsolete standalone prototype is removed, while supported demo APIs and fixtures remain. Demo routes live in `app/api/demo.py`; shared route authentication lives in `app/api/dependencies.py`. The unused OpenAI SDK dependency is removed; Ollama continues to use the existing local HTTP client.

- Runtime persistence uses local UTF-8 JSON files only; no database or ORM is included. Per-scan file locks, unique atomic temporary files, revision checks, and previous-revision backups protect concurrent updates.
- The current development environment is Windows with Python 3.14.2. The specification's reference environment is Ubuntu with Python 3.12, so live Linux route and Nmap checks remain pending.
- Nmap and Ollama are optional at startup. Demo and offline explanation tests do not require either external prerequisite.
- AI prepares the report overview and wording for all deterministic findings. Requests use a loopback Ollama endpoint and selected structured facts without network identifiers or raw output. Every accepted sentence is tied to reviewed alternatives; evidence, severity and rule-based actions stay authoritative. Original wording remains accessible.
- The web server is loopback-only. A bootstrap URL creates an expiring HTTP-only session; state-changing API calls also require an Origin check and CSRF token. The allowed scan network is server-owned and cannot be widened by a request.
- Collection saves its outcome before AI preparation. The visible job stays running through analysis; both dashboard and report page wait for it. New saved results, including empty and failed collections, enter analysis unless cancelled or the evidence size limit prevents further report updates. An unavailable model opens factual results with a visible retry message. The legacy `ai_enabled` setting is no longer a gate.
- AI uses batches of six with two attempts per batch and a 15-minute overall deadline including queue time. Accepted batches are checkpointed and reused. There is no 24-finding cutoff or lifetime request counter gate. A retry uses saved evidence and does not run Nmap.
- Optional mDNS discovery remains limited to the authorised IPv4 interface and eight unique hosts. The device table distinguishes advertisements, discovery responses and service responses. Names have source, timestamp, confidence and conflict metadata. Optional Pi-hole v6 names are read on the backend using environment-held credentials and never establish reachability.
- A host receives at most two attempts. Light Nmap/process deadlines are 180/210 seconds; Deep deadlines stay 900/960 seconds. Failure causes and attempt counts are stored. Retry unfinished checks creates a new scan of only eligible addresses, validated against the current authorised scope.
- Managed JSON reads and writes have the same 20 MiB UTF-8 byte limit, checked before replacing any checkpoint or backup. Guidance snapshots beyond three inline entries, or which would exceed that limit, are archived as referenced JSON files. Larger primary evidence is rejected explicitly and prior checkpoints stay readable.
- Saved reports can be reopened through `/history`. Storage retention/migration planning and the evaluation protocol are documented separately; no automatic deletion is enabled. Ubuntu lab and human-reader evaluation require the actual environment and participants.
