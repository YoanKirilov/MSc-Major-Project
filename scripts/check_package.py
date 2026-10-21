"""Build and verify a wheel in a fresh environment; never scan the network."""

import argparse
import os
import shutil
import subprocess
import venv
from pathlib import Path
from uuid import uuid4

if __package__:
    from .bootstrap_trust import bootstrap_trust
else:
    from bootstrap_trust import bootstrap_trust


def source_snapshot(root: Path, destination: Path) -> Path:
    """Never let stale checkout build/lib files reintroduce removed modules."""
    destination.mkdir(parents=True, exist_ok=False)
    for name in ("pyproject.toml", "README.md"):
        shutil.copy2(root / name, destination / name)
    shutil.copytree(
        root / "app",
        destination / "app",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wheelhouse", type=Path, help="Local directory containing dependency wheels"
    )
    parser.add_argument(
        "--offline", action="store_true", help="Use only --wheelhouse; no index access"
    )
    args = parser.parse_args(argv)
    if args.offline and args.wheelhouse is None:
        parser.error("--offline requires --wheelhouse with all pinned dependency wheels")
    if args.wheelhouse is not None and not args.wheelhouse.is_dir():
        parser.error("--wheelhouse must be an existing directory")
    install_options = []
    if args.offline:
        install_options.append("--no-index")
    if args.wheelhouse is not None:
        install_options.extend(["--find-links", str(args.wheelhouse.resolve())])
    root = Path(__file__).resolve().parents[1]
    run = root / ".test-artifacts" / f"package-{uuid4().hex[:10]}"
    run.mkdir(parents=True)
    print(f"Package verification artifacts: {run}", flush=True)
    source = source_snapshot(root, run / "source")

    def environment_python(name):
        environment = run / name
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        bootstrap_trust(python, args.wheelhouse or run / "trust-wheels", offline=args.offline)
        return python

    # Install a pinned backend into an owned environment instead of letting build
    # resolve unbounded backend versions or changing the running app environment.
    builder = environment_python("build-venv")
    subprocess.run(
        [
            str(builder),
            "-m",
            "pip",
            "install",
            *install_options,
            "-r",
            str(root / "requirements-build.lock"),
        ],
        check=True,
    )
    subprocess.run([str(builder), "-m", "pip", "check"], check=True)
    wheels = run / "wheels"
    subprocess.run(
        [str(builder), "-m", "build", "--no-isolation", "--wheel", "--outdir", str(wheels)],
        cwd=source,
        check=True,
    )
    python = environment_python("venv")
    built = list(wheels.glob("*.whl"))
    if len(built) != 1:
        raise RuntimeError("Expected exactly one project wheel")
    wheel = built[0]
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            *install_options,
            "-r",
            str(root / "requirements.lock"),
            "-r",
            str(root / "requirements-testclient.lock"),
            str(wheel),
        ],
        check=True,
    )
    subprocess.run([str(python), "-m", "pip", "check"], check=True)
    subprocess.run(
        [str(python), "-I", str(root / "scripts/verify_package.py")], cwd=run, check=True
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
