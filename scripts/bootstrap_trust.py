"""Hash-pinned, stdlib-only trust bootstrap. Never disable TLS or install from an index."""

import argparse
import hashlib
import os
import subprocess
import tempfile
import urllib.request
from pathlib import Path

# Independently checked against PyPI release metadata and the PSF incident notice.
# https://pypi.org/pypi/pip/26.2.2/json
# https://pypi.org/pypi/certifi/2026.10.19/json
WHEELS = (
    (
        "pip-26.2.2-py3-none-any.whl",
        "https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl",
        # Public release checksum, not a credential.
        # pragma: allowlist nextline secret
        "fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70",
    ),
    (
        "certifi-2026.10.19-py3-none-any.whl",
        "https://files.pythonhosted.org/packages/c4/51/29046e48f693c54e5b7412216d447a1d8362c9653148d98c02cdf65fa733/certifi-2026.10.19-py3-none-any.whl",
        # Public release checksum, not a credential.
        # pragma: allowlist nextline secret
        "42d35340cc5b9ba78e818ddbff0c5b1c2b779de448a340fd1b989f5fa8670e1b",
    ),
)
MAX_WHEEL_BYTES = 4 * 1024 * 1024


class _HttpsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if not newurl.startswith("https://files.pythonhosted.org/"):
            raise ValueError("Trust bootstrap redirect left the pinned HTTPS host")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def verified_wheels(folder, *, offline=False):
    folder = Path(folder)
    if folder.is_symlink():
        raise ValueError("Trust wheelhouse must not be a symlink")
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for filename, url, expected in WHEELS:
        path = folder / filename
        if path.is_symlink():
            raise ValueError("Trust wheel must not be a symlink")
        if path.exists():
            if not path.is_file() or path.stat().st_size > MAX_WHEEL_BYTES:
                raise ValueError("Invalid trust wheel")
            payload = path.read_bytes()
        else:
            if offline:
                raise ValueError(f"Offline bootstrap requires verified wheel: {filename}")
            with urllib.request.build_opener(_HttpsOnly()).open(url, timeout=30) as response:
                payload = response.read(MAX_WHEEL_BYTES + 1)
        if len(payload) > MAX_WHEEL_BYTES or hashlib.sha256(payload).hexdigest() != expected:
            raise ValueError(f"Trust wheel hash/size verification failed: {filename}")
        if not path.exists():
            fd, temporary = tempfile.mkstemp(prefix=".trust-", dir=folder)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, path)
            finally:
                Path(temporary).unlink(missing_ok=True)
        paths.append(path.resolve())
    return paths


def bootstrap_trust(python, folder, *, offline=False):
    wheels = verified_wheels(folder, offline=offline)
    subprocess.run(
        [
            str(python),
            "-I",
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "install",
            "--no-index",
            "--no-deps",
            "--upgrade",
            *map(str, wheels),
        ],
        check=True,
        timeout=120,
    )
    subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "import importlib.metadata as m; import pip._vendor.certifi as c; "
            "assert m.version('pip') == '26.2.2'; "
            "assert m.version('certifi') == '2026.10.19'; "
            "assert tuple(map(int,c.__version__.split('.'))) >= (2026,10,18); "
            "print('Verified pip, standalone certifi and pip-vendored trust bundle.')",
        ],
        check=True,
        timeout=20,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", help="Explicit target interpreter; no global default")
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if args.prepare_only:
        verified_wheels(args.wheelhouse, offline=args.offline)
    elif args.python:
        bootstrap_trust(args.python, args.wheelhouse, offline=args.offline)
    else:
        parser.error("Specify --python or --prepare-only; no environment changed")


if __name__ == "__main__":
    main()
