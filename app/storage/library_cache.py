"""Bounded per-store search projections; source JSON remains authoritative."""

import json
from collections import OrderedDict
from threading import RLock
from types import SimpleNamespace


def _fingerprint(folder):
    result = []
    for name in ("scan.json", "terminal.json"):
        path = folder / name
        if path.is_symlink():
            raise ValueError("Search source must not be a symlink")
        try:
            stat = path.stat()
            result.append((stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size, stat.st_ino))
        except FileNotFoundError:
            if name == "scan.json":
                raise
            result.append(None)
    return tuple(result)


def _compact(document):
    # Only retain fields required by search, identity matching and the picker.
    data = document.model_dump(
        include={
            "scan_id": True,
            "revision": True,
            "source": True,
            "created_at": True,
            "state": True,
            "phase": True,
            "analysis_status": True,
            "policy": True,
            "target": True,
            "devices": {
                "__all__": {
                    "device_id",
                    "ip",
                    "mac",
                    "hostname",
                    "vendor",
                    "observed_at",
                    "profile",
                    "reachability",
                    "discovery_method",
                }
            },
            "coverage": {"targets": {"__all__": {"ip", "service_status", "reason_code"}}},
            "findings": {"__all__": {"title"}},
        }
    )
    # Strings/collections in observations are not all schema-bounded; also bound bytes.
    size = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    projection = json.loads(json.dumps(data), object_hook=lambda obj: SimpleNamespace(**obj))
    # Nickname matching and filtering expect ordinary policy/target mappings.
    projection.policy = data["policy"]
    projection.target = data["target"]
    return projection, size


class LibraryCache:
    """Rebuilt after restart; never caches names, titles, failures or unstable files."""

    def __init__(self, max_entries=512, max_bytes=8 * 1024 * 1024):
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self.entries = OrderedDict()
        self.size = 0
        self.lock = RLock()
        self.preferred = None

    def prefer(self, scan_ids):
        """Admit a stable recent hot set during full-library sweeps, not every miss.

        Otherwise a library just larger than the cache evicts every entry on
        every sequential search. No projection or source stamp becomes authoritative.
        """
        with self.lock:
            self.preferred = {
                str(value): index for index, value in enumerate(scan_ids[: self.max_entries])
            }
            for key in list(self.entries):
                if key not in self.preferred:
                    self.size -= self.entries.pop(key)[2]

    def load(self, store, scan_id):
        with self.lock:
            folder = store._scan_dir(scan_id)
            key = str(scan_id)
            stamp = _fingerprint(folder)
            cached = self.entries.pop(key, None)
            if cached:
                self.size -= cached[2]
                if cached[0] == stamp:
                    self.entries[key] = cached
                    self.size += cached[2]
                    return cached[1]
            projection, size = _compact(store._load_scan(scan_id))
            if (
                stamp == _fingerprint(folder)
                and size <= self.max_bytes
                and (self.preferred is None or key in self.preferred)
            ):
                if self.preferred is not None:
                    rank = self.preferred[key]
                    removable = sorted(
                        (entry for entry in self.entries if self.preferred[entry] > rank),
                        key=self.preferred.get,
                        reverse=True,
                    )
                    if (
                        self.size - sum(self.entries[entry][2] for entry in removable) + size
                        > self.max_bytes
                        or len(self.entries) - len(removable) >= self.max_entries
                    ):
                        return projection
                    for entry in removable:
                        if (
                            self.size + size <= self.max_bytes
                            and len(self.entries) < self.max_entries
                        ):
                            break
                        self.size -= self.entries.pop(entry)[2]
                self.entries[key] = (stamp, projection, size)
                self.size += size
                while len(self.entries) > self.max_entries or self.size > self.max_bytes:
                    _, removed = self.entries.popitem(last=False)
                    self.size -= removed[2]
            return projection
