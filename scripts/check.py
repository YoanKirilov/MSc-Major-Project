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
    parser.add_argument("--browser", action="store_true", help="Use a browser with synthetic scans")
    parser.add_argument(
        "--ollama", action="store_true", help="Test local Ollama on synthetic facts"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if shutil.which("node") is None:
        parser.error("Node.js is required for the JavaScript checks")
    run = root / ".test-artifacts" / f"checks-{uuid4().hex[:10]}"
    run.mkdir(parents=True)
    env = os.environ.copy()
    # Explicit opt-ins override any flags left in the parent shell.
    env["RUN_BROWSER_TESTS"] = "1" if args.browser else "0"
    env["RUN_LIVE_OLLAMA"] = "1" if args.ollama else "0"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["RUFF_CACHE_DIR"] = str(run / "ruff-cache")
    selection = "not live_lab and not human_study"
    if not args.browser:
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
        ],
        ["node", "tests/dashboard_ui.test.mjs"],
        ["node", "tests/report_ui.test.mjs"],
        ["node", "tests/live_server_bridge.test.mjs"],
        *[
            ["node", "--check", str(path)]
            for path in sorted((root / "app/static/js").iterdir())
            if path.suffix in {".js", ".mjs"}
        ],
    ]
    print(f"Check artifacts: {run}", flush=True)
    for command in commands:
        print(f"Running: {subprocess.list2cmdline(command)}", flush=True)
        result = subprocess.run(command, cwd=root, env=env, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
