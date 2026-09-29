# Repeatable release checks

Updated 29 September 2026. These are local prototype checks, not certification.
Use separate virtual environments; do not install security tooling into the running app.

## Regression, browser and package checks

```powershell
python -m venv .venv-quality
.\.venv-quality\Scripts\python.exe -m pip install -r requirements-dev.lock -e ".[dev]"
.\.venv-quality\Scripts\python.exe -m playwright install chromium firefox webkit
.\.venv-quality\Scripts\python.exe scripts/check.py --browser --browser-engines chromium,firefox,webkit
.\.venv-quality\Scripts\python.exe scripts/check_package.py
```

The responsive matrix covers four pages at 320x568, 390x844, 844x390, 768x1024,
1024x768, 1280x720, 1920x1080 and 2560x1440 CSS pixels in three engines. It checks
page overflow, long device names, first-action placement, report counts, finding
selection and the Deep Run again dialog. Additional checks cover 200% text size,
keyboard focus and Chromium/WebKit mobile touch emulation. Narrow CSS viewports are
reflow approximations, not actual browser-zoom or physical-device certification.
Firefox uses desktop viewport emulation. Real iOS Safari/Android devices and assistive
technology testing remain pending. No synthetic browser test runs Nmap or contacts devices.

## Security gates

```powershell
python -m venv .venv-quality-security
.\.venv-quality-security\Scripts\python.exe -m pip install -r requirements-security.lock
.\.venv-quality-security\Scripts\python.exe scripts/check_security.py
```

- [pip-audit](https://github.com/pypa/pip-audit) checks pinned runtime/development
  dependencies. PyPI receives package names and versions, not source or scan evidence.
  Advisories block the gate; no automatic dependency fixes or ignored advisory IDs.
- [Bandit](https://github.com/PyCQA/bandit) scans application Python locally. Medium/high
  findings block the gate; all low findings remain in the JSON report for review.
- [detect-secrets](https://github.com/Yelp/detect-secrets) scans tracked and non-ignored
  new files locally, with credential verification disabled. Any remaining alert blocks
  the gate. It does not scan Git history or ignored private configuration.

Reports are saved under an ignored `.test-artifacts/security-*` folder. Never publish
raw security reports or home-network artifacts automatically. Missing tools, unavailable
advisory services and malformed output fail the check rather than imply a clean scan.
Exact pins are retained for tools; hashes/reproducible build tooling remain future work.

### Findings reviewed on 29 September

The original dependency audit reported two copies of the same pytest advisory,
`PYSEC-2026-1845` / `CVE-2025-71176`, for pytest 8.4.2. It concerns shared temporary
directories on UNIX. Updated the development constraints/pins to pytest 9.0.3 and
pytest-asyncio 1.4.0, validated in a fresh environment. Runtime requirements are unchanged.
The updated dependency audit found no known advisories. This is not proof of no defects.

Twelve low Bandit alerts were reviewed, without global suppressions:

- B404/B603 in `app/config.py`: subprocess import and fixed argument-array calls for
  local route/Nmap checks. No shell expansion; scope and configuration remain validated.
- B607 for `ipconfig` / `ip`: trusted system tools are located through the operator's
  PATH. Residual risk: run only with a trusted PATH/workspace; privileged multi-user
  deployment would require stronger executable resolution. Not a new remote exploit.
- B110 in `app/cli.py`: opening a browser is best-effort; the local session link remains
  available if opening fails.
- B112 in storage enumeration: malformed reports are skipped for job reconciliation,
  not declared successful; history/audit expose unreadable reports.

Five secret alerts were reviewed: four deliberate synthetic test credentials and the
Pi-hole password-file reference. Only those exact lines have explanatory allowlist
comments. No real credential was exposed, verified online or broadly excluded.

## Copied-backup recovery drill

```powershell
.\.venv-quality\Scripts\python.exe scripts/check_restore.py --data-dir "<saved-data-root>" --scan-id "<uuid>"
```

Select a finished report with `scan.previous.json`. The drill copies its folder to a new
ignored artifact directory, corrupts only the copied primary, previews recovery, then
restores a separate report from the copied backup. It checks fact preservation and
source/copy hashes. It never repairs/deletes normal reports or starts the backend.
An older checkpoint may recover as incomplete; it must not pretend later work finished.
The real-report drill retained 12 devices and eight findings, marked the older checkpoint
partial, and left source and copied evidence unchanged. The recovered report is test data.

## Remaining external approvals/evaluation

CI now defines the browser matrix and a separate security job for future pushes/PRs.
No push, remote workflow dispatch or repository protection changes were performed here.
Remote Ubuntu results and required-check enforcement still need verification. Local WSL
is not installed. Pi-hole/live Deep evaluation requires its own configured environment.
The reader-study kit remains a protocol: real participant results, ethical approval and
independent scoring cannot be replaced by automated tests or assistant review.
