"""Non-secret, process-frozen build identity; never inferred from fresh static files."""

import hashlib
from pathlib import Path

from app.schemas.common import iso_z, utc_now

API_CONTRACT_VERSION = 3


def source_build_id(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in {".py", ".js", ".mjs", ".html", ".css"}:
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()[:20]


RUNNING_BUILD = {
    "build_id": source_build_id(),
    "contract_version": API_CONTRACT_VERSION,
    "started_at": iso_z(utc_now()),
}
