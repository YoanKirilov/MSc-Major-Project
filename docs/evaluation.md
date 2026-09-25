# Evaluation and remaining environment work

Automated checks establish software behaviour. They do not establish that nontechnical
people understand the report or that every device on a live network will answer.

## Reproducible installation

Use Python 3.12 on the intended Ubuntu lab host. In a new virtual environment, install
`python -m pip install -r requirements-dev.lock -e ".[dev]"`, then run `python -m pip check`.
The current pins were resolved and tested on Windows/Python 3.14; verify their Linux
wheels and compatibility before claiming the reference platform is supported.

Run the offline Python suite and the JavaScript tests described in `testing.md`.
Build a wheel with `python -m build --wheel`. Install the wheel and `requirements.lock`
in another environment and run it from outside the source checkout. Check `/`,
`/settings`, `/history`, a report page and each referenced static asset.

## Browser workflow

Set `RUN_BROWSER_TESTS=1` and run `pytest tests/browser_test_workflow.py`.
The default channel is installed Microsoft Edge; on Linux run `python -m playwright install chromium`
and set `BROWSER_CHANNEL` to an empty string to use the downloaded Chromium.
This test uses a real browser with synthetic scanner/provider responses and isolated
JSON files. It covers waiting for AI, a completed report, an AI outage with factual
results visible, retry without scanning, saved history and a Light known-host rescan.

## Live lab protocol

Record authorisation, interface, exact private subnet and one known test-host IP before
testing. Verify that saved scope and active interface agree. This development session
found a saved `192.168.0.0/24` scope but detection reported `192.168.91.0/24`; neither
range should be assumed to be the next authorised target.

Use `APP_DATA_DIR` pointing to a new test folder. Confirm Nmap/Npcap or Linux scan
permissions, start Ollama and confirm the configured model. Run a Light known-host
scan first. Record target/profile, versions, elapsed time, terminal collection state,
per-host attempts/reasons, device/service counts and AI status. Compare service claims
with independently known host configuration. Then test cancellation, a deliberately
unreachable lab host and retry of unfinished checks. Run Deep only against the single
approved lab VM and compare its known services. Keep scan JSON private and sanitise
identifiers before including evidence in the dissertation.

A timeout is a result about coverage, not a passed security check. Report which checks
completed and which could not. Pi-hole integration additionally needs a real v6 instance
and its API credentials; compare imported names with its DHCP/network table and test an
expired/reassigned address. A router import needs a documented vendor API or a sample
DHCP/client export; there is no single format supported by all routers. Routing tables
alone do not provide a reliable list of device names.

## Nontechnical-reader study

Recruit participants who do not work in computing, using the university's required
consent/ethics process. Use synthetic examples: an observed service needing review,
zero findings, no responding devices, an incomplete scan and an AI outage. Do not use
participants' home-network identifiers. Counterbalance whether they see original or
AI-selected wording first, using the same underlying facts.

Ask each participant, in their own words:

1. What did the scan actually find?
2. What did it not check or establish?
3. Which step would you take first, and why?
4. Does the report prove the device is safe or has been hacked?
5. Which words or screen elements were confusing?

Record anonymous participant ID, report condition, correct answers (0/1 for the first
four questions), time to answer, clarity rating (1–5), confidence and free-text comments.
Have a second reviewer check a sample of the answer scoring. Compare comprehension,
time and misleading interpretations; a higher clarity rating alone is insufficient.
Use the findings to revise reviewed wording and rerun the relevant cases. The study
has not yet been conducted; no participant responses or effectiveness claims are fabricated.
