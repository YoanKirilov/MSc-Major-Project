"""Build and verify a wheel in a fresh environment; never scan the network."""

import os
import subprocess
import sys
import venv
from pathlib import Path
from uuid import uuid4


def main():
    root = Path(__file__).resolve().parents[1]
    run = root / ".test-artifacts" / f"package-{uuid4().hex[:10]}"
    run.mkdir(parents=True)
    wheels = run / "wheels"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(wheels)], cwd=root, check=True
    )
    environment = run / "venv"
    venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    wheel = next(wheels.glob("*.whl"))
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
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
    print(f"Package verification artifacts: {run}")


if __name__ == "__main__":
    main()
