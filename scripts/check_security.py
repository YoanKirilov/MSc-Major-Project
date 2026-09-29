"""Audit pinned dependencies and source; keep private evidence out of uploads."""

import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / ".test-artifacts" / f"security-{uuid4().hex[:10]}"
    output.mkdir(parents=True)
    print(f"Security artifacts: {output}", flush=True)
    # PyPI receives package names/versions only. No automatic fixes or ignore IDs.
    audit = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip_audit",
            "-r",
            "requirements-dev.lock",
            "--no-deps",
            "--disable-pip",
            "-f",
            "json",
            "-o",
            str(output / "dependencies.json"),
        ],
        cwd=root,
        timeout=600,
        check=False,
    )
    static = subprocess.run(
        [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            "app",
            "-f",
            "json",
            "-o",
            str(output / "static.json"),
        ],
        cwd=root,
        timeout=120,
        check=False,
    )
    # Include untracked new code, but never ignored .env/venv/report folders.
    files = (
        subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=root)
        .decode()
        .split("\0")
    )
    files = sorted({name for name in files if name and (root / name).is_file()})
    secrets = subprocess.run(
        [sys.executable, "-m", "detect_secrets", "scan", "--no-verify", "--all-files", *files],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if secrets.returncode:
        print("Secret scan could not complete; no clean result is claimed.")
        return 1
    secret_data = json.loads(secrets.stdout)
    (output / "secrets.json").write_text(json.dumps(secret_data, indent=2), encoding="utf-8")
    static_data = json.loads((output / "static.json").read_text(encoding="utf-8"))
    findings = static_data.get("results", [])
    # All low findings remain in the report for review; medium/high block this gate.
    blocking = [item for item in findings if item["issue_severity"] in {"MEDIUM", "HIGH"}]
    secret_count = sum(len(items) for items in secret_data.get("results", {}).values())
    print(f"Static findings: {len(findings)} ({len(blocking)} medium/high).")
    print(f"Potential secrets: {secret_count}. Values are never printed or verified online.")
    # Missing scans, unexpected errors and any potential secret fail closed.
    return int(
        bool(
            audit.returncode
            or static.returncode not in {0, 1}
            or static_data.get("errors")
            or blocking
            or secret_count
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
