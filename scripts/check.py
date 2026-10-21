"""Repeatable checks with all new artifacts in one ignored directory. No network scans."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--browser", action="store_true", help="Use a browser with synthetic scans")
    modes.add_argument(
        "--browser-only",
        action="store_true",
        help="Only selected-engine synthetic browser tests (offline gate is separate)",
    )
    parser.add_argument(
        "--ci-artifacts",
        action="store_true",
        help="Export bounded, redacted synthetic failure diagnostics and JUnit",
    )
    parser.add_argument(
        "--browser-engines",
        default="chromium",
        help="Responsive engines: chromium,firefox,webkit (install first)",
    )
    parser.add_argument(
        "--ollama", action="store_true", help="Test local Ollama on synthetic facts"
    )
    args = parser.parse_args()
    if any(
        engine not in {"chromium", "firefox", "webkit"}
        for engine in args.browser_engines.split(",")
    ):
        parser.error("Unknown browser engine")
    root = Path(__file__).resolve().parents[1]
    if shutil.which("node") is None:
        parser.error("Node.js is required for the JavaScript checks")
    run = root / ".test-artifacts" / f"checks-{uuid4().hex[:10]}"
    run.mkdir(parents=True)
    env = os.environ.copy()
    # Explicit opt-ins override any flags left in the parent shell.
    use_browser = args.browser or args.browser_only
    env["RUN_BROWSER_TESTS"] = "1" if use_browser else "0"
    env["RESPONSIVE_BROWSERS"] = args.browser_engines
    env["UI_UX_BROWSERS"] = args.browser_engines
    env["RUN_LIVE_OLLAMA"] = "1" if args.ollama else "0"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["RUFF_CACHE_DIR"] = str(run / "ruff-cache")
    selection = "not live_lab and not human_study"
    if args.browser_only:
        selection += " and browser"
    elif not args.browser:
        selection += " and not browser"
    if not args.ollama:
        selection += " and not live_provider"
    commands = [
        [sys.executable, "-m", "ruff", "check", "app", "tests", "scripts"],
        [sys.executable, "-m", "ruff", "format", "--check", "app", "tests", "scripts"],
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            selection,
            "--basetemp",
            str(run / "pytest"),
            "-o",
            f"cache_dir={run / 'pytest-cache'}",
            "--tb=short",
            "--durations=15",
            f"--junitxml={run / 'pytest-results.xml'}",
        ],
        ["node", "tests/api_ui.test.mjs"],
        ["node", "tests/appearance_ui.test.mjs"],
        ["node", "tests/dashboard_ui.test.mjs"],
        ["node", "tests/setup_tools_ui.test.mjs"],
        ["node", "tests/history_ui.test.mjs"],
        ["node", "tests/history_management_ui.test.mjs"],
        ["node", "tests/report_ui.test.mjs"],
        ["node", "tests/report_view_ui.test.mjs"],
        ["node", "tests/report_device_context_ui.test.mjs"],
        ["node", "tests/editor_ui.test.mjs"],
        ["node", "tests/notes_ui.test.mjs"],
        ["node", "tests/nicknames_ui.test.mjs"],
        ["node", "tests/device_components_ui.test.mjs"],
        ["node", "tests/report_insights_ui.test.mjs"],
        ["node", "tests/report_export_ui.test.mjs"],
        ["node", "tests/device_library_ui.test.mjs"],
        ["node", "tests/device_library_context_ui.test.mjs"],
        ["node", "tests/live_server_bridge.test.mjs"],
        *[
            ["node", "--check", str(path)]
            for path in sorted((root / "app/static/js").iterdir())
            if path.suffix in {".js", ".mjs"}
        ],
    ]
    if args.browser_only:
        commands = [command for command in commands if "pytest" in command]
    if args.ci_artifacts:
        export = root / ".test-artifacts" / "ci-reports" / run.name
        export.mkdir(parents=True, exist_ok=False)
        env["NETGUARD_DIAGNOSTICS_DIR"] = str(export)
    print(f"Check artifacts: {run}", flush=True)
    for command in commands:
        print(f"Running: {subprocess.list2cmdline(command)}", flush=True)
        result = subprocess.run(command, cwd=root, env=env, check=False)
        if args.ci_artifacts and "pytest" in command:
            junit = run / "pytest-results.xml"
            if junit.is_file() and junit.stat().st_size <= 10 * 1024 * 1024:
                shutil.copy2(junit, export / "pytest-results.xml")
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
