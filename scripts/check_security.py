"""Audit pinned dependencies and source; keep private evidence out of uploads."""

import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def audit_requirements(root, entry="requirements-dev.lock"):
    """Flatten the pinned include graph; the no-install audit ignores -r includes."""
    pending = [root / entry]
    visited, pins, lines = set(), {}, set()
    while pending:
        path = pending.pop().resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Dependency lock includes must remain inside the project")
        if path in visited:
            continue
        visited.add(path)
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("-r "):
                pending.append(path.parent / line[3:].strip())
                continue
            requirement = Requirement(line)
            specifiers = list(requirement.specifier)
            if (
                requirement.url
                or len(specifiers) != 1
                or specifiers[0].operator != "=="
                or "*" in specifiers[0].version
            ):
                raise ValueError("Dependency audits require exact version pins")
            name, version = canonicalize_name(requirement.name), specifiers[0].version
            if name in pins and pins[name] != version:
                raise ValueError(f"Conflicting dependency pins for {name}")
            pins[name] = version
            lines.add(str(requirement))
    if not lines:
        raise ValueError("No pinned dependencies found for audit")
    return sorted(lines)


def audit_covers(requirements, document):
    """Do not let ignored includes/skipped packages produce a false clean result."""
    expected = set()
    for line in requirements:
        requirement = Requirement(line)
        if requirement.marker is None or requirement.marker.evaluate():
            expected.add(
                (canonicalize_name(requirement.name), next(iter(requirement.specifier)).version)
            )
    try:
        actual = {
            (canonicalize_name(item["name"]), item["version"])
            for item in document["dependencies"]
            if "version" in item
        }
    except (KeyError, TypeError, ValueError, AttributeError):
        return False
    return bool(expected) and expected <= actual


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / ".test-artifacts" / f"security-{uuid4().hex[:10]}"
    output.mkdir(parents=True)
    print(f"Security artifacts: {output}", flush=True)
    # Tooling lives in a different environment and can legitimately have other
    # versions of runtime packages. Validate each graph independently, audit both.
    audit_codes = []
    for entry, report in (
        ("requirements-dev.lock", "dependencies.json"),
        ("requirements-security.lock", "tool-dependencies.json"),
    ):
        pins = audit_requirements(root, entry)
        path = output / entry.replace(".lock", "-audit.txt")
        path.write_text("\n".join(pins) + "\n", encoding="utf-8")
        # Audit independently: pip-audit rejects different versions across inputs,
        # even when they belong to legitimately separate installed environments.
        # PyPI receives package names/versions only. No automatic fixes or ignores.
        audit = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip_audit",
                "-r",
                str(path),
                "--no-deps",
                "--disable-pip",
                "-f",
                "json",
                "-o",
                str(output / report),
            ],
            cwd=root,
            timeout=600,
            check=False,
        )
        audit_codes.append(audit.returncode)
        try:
            covered = audit_covers(pins, json.loads((output / report).read_text(encoding="utf-8")))
        except (OSError, ValueError):
            covered = False
        if not covered:
            print(f"Dependency audit coverage incomplete for {entry}; gate fails closed.")
            audit_codes.append(1)
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
            any(audit_codes)
            or static.returncode not in {0, 1}
            or static_data.get("errors")
            or blocking
            or secret_count
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
