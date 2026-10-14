"""Bounded, rebuildable device inventory with separate household labels."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address, ip_network
from uuid import UUID

from app.scanner.names import clean_name, normalise_mac
from app.schemas.common import StrictModel, iso_z, observation_time
from app.schemas.projections import HistorySummary
from app.security.scope import PRIVATE_NETWORKS
from filelock import FileLock
from pydantic import Field, StrictBool, StrictInt, field_validator

from .nicknames import NicknameDocument
from .report_trash import ReportTrash, UnsafeReportPath

DEVICE_KEY_PATTERN = r"d-[a-f0-9]{64}"
MAX_DIRECTORY_ENTRIES = 2000
MAX_REPORTS = 200
MAX_EVIDENCE_BYTES = 64 * 1024 * 1024
MAX_DEVICE_OBSERVATIONS = 4096
MAX_REPORT_LINKS = 24
MAX_LABEL_ENTRIES = 4096
MAX_LABEL_BYTES = 1024 * 1024
MAX_SUMMARY_BYTES = 16 * 1024
FINISHED_STATES = {"completed", "partial", "failed", "cancelled"}


class LabelsUnavailable(ValueError):
    pass


class LabelRevisionConflict(ValueError):
    pass


class UnknownDevice(ValueError):
    pass


class LabelCapacityExceeded(ValueError):
    pass


class DeviceLabels(StrictModel):
    room: str = Field(default="", max_length=80)
    favourite: StrictBool = False
    recognised: StrictBool = False

    @field_validator("room")
    @classmethod
    def single_line(cls, value):
        if any(not char.isprintable() for char in value):
            raise ValueError("Use a single line for the room")
        return value.strip()


class DeviceLabelUpdate(DeviceLabels):
    expected_revision: StrictInt = Field(ge=1)


class DeviceLabelDocument(StrictModel):
    revision: StrictInt = Field(default=1, ge=1)
    entries: dict[str, DeviceLabels] = Field(default_factory=dict, max_length=MAX_LABEL_ENTRIES)

    @field_validator("entries")
    @classmethod
    def validate_keys(cls, value):
        if any(not re.fullmatch(DEVICE_KEY_PATTERN, key) for key in value):
            raise ValueError("Invalid device label key")
        return value


def _key(*parts: str) -> str:
    payload = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return "d-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _scope(document):
    try:
        value = document.policy.get("allowed_network")
        if not isinstance(value, str):
            return None
        network = ip_network(value, strict=False)
        if network.version != 4 or not any(network.subnet_of(item) for item in PRIVATE_NETWORKS):
            return None
        return network
    except ValueError:
        return None


def _usable_mac(value):
    mac = normalise_mac(value)
    if not mac or mac == "00:00:00:00:00:00" or int(mac[:2], 16) & 1:
        return None
    return mac


class DeviceInventory:
    def __init__(self, store):
        self.store = store
        self.path = store.data_root / "device-labels.json"
        self.backup = store.data_root / "device-labels.previous.json"
        self.lock_path = store.data_root / "device-labels.lock"
        self.lock = FileLock(str(self.lock_path), timeout=5)
        self.safety = ReportTrash(store)

    def _safe_paths(self):
        root = self.store.data_root.resolve()
        for path in (self.path, self.backup, self.lock_path):
            try:
                self.safety._safe_path(path)
            except UnsafeReportPath as exc:
                raise LabelsUnavailable("Household labels use an unsafe local path") from exc
            if path.resolve().parent != root:
                raise LabelsUnavailable("Household labels use an unsafe local path")
            if path.exists() and not path.is_file():
                raise LabelsUnavailable("Household labels use an unsafe local path")

    def _labels_locked(self):
        self._safe_paths()
        if not self.path.exists():
            if self.backup.exists():
                raise LabelsUnavailable("Household labels require recovery from their backup")
            return DeviceLabelDocument()
        try:
            if self.path.stat().st_size > MAX_LABEL_BYTES:
                raise ValueError("Household labels exceed the size limit")
            return DeviceLabelDocument.model_validate(self.store._read_json(self.path), strict=True)
        except (OSError, ValueError) as exc:
            raise LabelsUnavailable("Household labels could not be read safely") from exc

    def _labels(self):
        self._safe_paths()
        with self.lock:
            return self._labels_locked()

    def _candidates(self, warnings):
        """Use cheap validated summaries; only the bounded newest candidates load evidence."""
        folder = self.store.data_root / "scans"
        try:
            self.safety._safe_path(folder)
        except UnsafeReportPath:
            warnings.add("Saved report folders could not be read safely; inventory is incomplete.")
            return []
        if not folder.exists():
            return []
        if (
            folder.is_symlink()
            or not folder.is_dir()
            or folder.resolve().parent != self.store.data_root.resolve()
        ):
            warnings.add("Saved report folders could not be read safely; inventory is incomplete.")
            return []
        candidates = []
        floor = datetime.min.replace(tzinfo=timezone.utc)
        for index, scan_dir in enumerate(folder.iterdir()):
            if index >= MAX_DIRECTORY_ENTRIES:
                warnings.add(
                    "The saved report folder limit was reached; some devices and dates may be "
                    "missing from this inventory."
                )
                break
            try:
                scan_id = str(UUID(scan_dir.name))
                self.safety._safe_path(scan_dir)
                if (
                    scan_id != scan_dir.name
                    or scan_dir.is_symlink()
                    or not scan_dir.is_dir()
                    or scan_dir.resolve().parent != folder.resolve()
                ):
                    continue
                primary = scan_dir / "scan.json"
                self.safety._safe_path(primary)
                if primary.is_symlink() or not primary.is_file():
                    warnings.add("Some saved reports could not be read safely and were omitted.")
                    continue
                summary_file = scan_dir / "summary.json"
                stamp = None
                try:
                    self.safety._safe_path(summary_file)
                    if (
                        not (scan_dir / "terminal.json").exists()
                        and not summary_file.is_symlink()
                        and summary_file.stat().st_size <= MAX_SUMMARY_BYTES
                        and summary_file.stat().st_mtime_ns >= primary.stat().st_mtime_ns
                    ):
                        summary = HistorySummary.model_validate(
                            self.store._read_json(summary_file), strict=True
                        )
                        if summary.scan_id != scan_id:
                            raise ValueError("Summary identity mismatch")
                        if summary.source != "live" or summary.state not in FINISHED_STATES:
                            continue
                        stamp = observation_time(summary.created_at)
                except (OSError, ValueError):
                    pass
                # A stale/missing summary is eligible for bounded full validation.
                fallback = datetime.fromtimestamp(primary.stat().st_mtime, timezone.utc)
                candidates.append((stamp or fallback or floor, scan_id, primary))
            except (OSError, ValueError, OverflowError):
                warnings.add("Some saved reports could not be read safely and were omitted.")
        return sorted(candidates, key=lambda value: (value[0], value[1]), reverse=True)

    def _nicknames(self, warnings):
        path = self.store.data_root / "nicknames.json"
        backup = path.with_name("nicknames.previous.json")
        if not path.exists() and not path.is_symlink() and not backup.exists():
            return {}
        try:
            self.safety._safe_path(path)
            if path.stat().st_size > MAX_LABEL_BYTES:
                raise ValueError("Nickname file exceeds inventory read limit")
            saved = NicknameDocument.model_validate(self.store._read_json(path))
            if saved.recovery_notice:
                warnings.add(saved.recovery_notice)
            return {
                (str(entry.scan_id), str(entry.device_id)): entry.nickname
                for entry in saved.entries
            }
        except (OSError, ValueError):
            warnings.add("Saved nicknames could not be read; some device names may be missing.")
            return {}

    def _facts(self):
        warnings = set()
        nicknames = self._nicknames(warnings)
        groups = {}
        read_bytes, observations = 0, 0
        candidates = self._candidates(warnings)
        if len(candidates) > MAX_REPORTS:
            warnings.add(
                f"Inventory reads at most {MAX_REPORTS} recent report candidates; older devices "
                "and earlier dates may be missing."
            )
        for _stamp, scan_id, path in candidates[:MAX_REPORTS]:
            try:
                self.safety._safe_path(path.parent)
                self.safety._safe_path(path)
                size = path.stat().st_size
                terminal = path.with_name("terminal.json")
                self.safety._safe_path(terminal)
                if terminal.exists():
                    if terminal.is_symlink() or not terminal.is_file():
                        raise ValueError("Unsafe terminal status path")
                    size += terminal.stat().st_size
                if read_bytes + size > MAX_EVIDENCE_BYTES:
                    warnings.add(
                        "The report read limit was reached; older devices and earlier dates "
                        "may be missing."
                    )
                    break
                read_bytes += size
                document = self.store._load_scan(scan_id)
            except (OSError, ValueError, TypeError):
                warnings.add("Some saved reports could not be read safely and were omitted.")
                continue
            if document.source != "live" or document.phase != "finished":
                continue
            if document.state not in FINISHED_STATES:
                continue
            scope = _scope(document)
            network = str(scope) if scope else None
            mac_counts = Counter(_usable_mac(device.mac) for device in document.devices)
            device_ips = {device.ip for device in document.devices}
            selected = {host for host in document.target.get("hosts", []) if isinstance(host, str)}
            unfinished_targets = [
                target
                for target in document.coverage.targets
                if target.ip not in device_ips
                and target.service_status != "completed"
                and (
                    target.discovery_status == "observed"
                    or document.target.get("mode") == "known_hosts"
                    and target.ip in selected
                )
            ]
            # A discovery-only duplicate also makes a completed device's MAC ambiguous.
            mac_counts.update(_usable_mac(target.discovery_mac) for target in unfinished_targets)
            id_counts = Counter(device.device_id for device in document.devices)
            findings = Counter(finding.device_id for finding in document.findings)
            checks = {target.ip: target.service_status for target in document.coverage.targets}
            for index, device in enumerate(document.devices):
                if observations >= MAX_DEVICE_OBSERVATIONS:
                    warnings.add(
                        "The device observation limit was reached; some inventory records "
                        "may be missing."
                    )
                    break
                observations += 1
                mac = _usable_mac(device.mac)
                in_scope = False
                try:
                    in_scope = scope is not None and ip_address(device.ip) in scope
                except ValueError:
                    pass
                stable = mac and mac_counts[mac] == 1 and in_scope
                device_key = (
                    _key("mac", network, mac)
                    if stable
                    else _key(
                        "observation",
                        scan_id,
                        device.device_id,
                        str(index) if id_counts[device.device_id] > 1 else "",
                    )
                )
                observed = observation_time(device.observed_at)
                created = observation_time(document.created_at)
                if observed is None:
                    warnings.add(
                        "Some observation dates could not be verified; those dates are shown "
                        "as unavailable."
                    )
                report = {
                    "scan_id": scan_id,
                    "device_id": device.device_id,
                    "created_at": document.created_at,
                    "state": document.state,
                }
                occurrence = {
                    "observed": observed,
                    "created": created,
                    "name": clean_name(device.hostname) or "Unnamed device",
                    "nickname": nicknames.get((scan_id, device.device_id)),
                    "ip": device.ip,
                    "review_count": findings[device.device_id],
                    "unfinished_count": int(
                        checks[device.ip] != "completed"
                        if device.ip in checks
                        else not document.coverage.service_stage_complete
                    ),
                    "report": report,
                }
                groups.setdefault(device_key, {"network": network, "occurrences": []})[
                    "occurrences"
                ].append(occurrence)
            target_counts = Counter(target.ip for target in unfinished_targets)
            for index, target in enumerate(unfinished_targets):
                if observations >= MAX_DEVICE_OBSERVATIONS:
                    warnings.add(
                        "The device observation limit was reached; some inventory records "
                        "may be missing."
                    )
                    break
                observations += 1
                created = observation_time(document.created_at)
                if created is None:
                    warnings.add(
                        "Some observation dates could not be verified; those dates are shown "
                        "as unavailable."
                    )
                device_key = _key(
                    "unfinished-target",
                    scan_id,
                    target.ip,
                    str(index) if target_counts[target.ip] > 1 else "",
                )
                identity_note = (
                    "Discovery only; device checks did not finish. This record is kept "
                    "separately because device identity was not established."
                    if target.discovery_status == "observed"
                    else "Selected address only; device checks did not finish and a response "
                    "was not established."
                )
                occurrence = {
                    "observed": created,
                    "created": created,
                    "name": clean_name(target.discovery_hostname) or "Unnamed device",
                    "nickname": None,
                    "ip": target.ip,
                    "review_count": 0,
                    "unfinished_count": 1,
                    "identity_note": identity_note,
                    "report": {
                        "scan_id": scan_id,
                        "device_id": None,
                        "created_at": document.created_at,
                        "state": document.state,
                    },
                }
                groups[device_key] = {"network": network, "occurrences": [occurrence]}
            if observations >= MAX_DEVICE_OBSERVATIONS:
                break
        floor = datetime.min.replace(tzinfo=timezone.utc)
        items = []
        for device_key, group in groups.items():
            occurrences = sorted(
                group["occurrences"],
                key=lambda item: (
                    item["observed"] or item["created"] or floor,
                    item["report"]["scan_id"],
                ),
                reverse=True,
            )
            latest = occurrences[0]
            name = latest["nickname"]
            if not name and latest["created"]:
                reusable = [
                    item["nickname"]
                    for item in occurrences[1:]
                    if item["nickname"]
                    and item["created"]
                    and timedelta(0) <= latest["created"] - item["created"] <= timedelta(days=7)
                ]
                if len(reusable) == 1:
                    name = reusable[0]
            times = [item["observed"] for item in occurrences if item["observed"]]
            reports = []
            seen_reports = set()
            for item in occurrences:
                if item["report"]["scan_id"] not in seen_reports:
                    reports.append(item["report"])
                    seen_reports.add(item["report"]["scan_id"])
            if len(reports) > MAX_REPORT_LINKS:
                warnings.add(
                    f"Each device shows at most {MAX_REPORT_LINKS} recent saved report links."
                )
            item = {
                "device_key": device_key,
                "display_name": name or latest["name"],
                "last_ip": latest["ip"],
                "network": group["network"],
                "first_observed": iso_z(min(times)) if times else None,
                "last_observed": iso_z(max(times)) if times else None,
                "report_count": len(reports),
                "review_count": latest["review_count"],
                "unfinished_count": latest["unfinished_count"],
                "reports": reports[:MAX_REPORT_LINKS],
            }
            if latest.get("identity_note"):
                item["identity_note"] = latest["identity_note"]
            items.append(item)
        return items, warnings

    def list(self, *, offset=0, limit=24, search="", view="all"):
        if view not in {"all", "favourites", "not-recognised", "unfinished", "review"}:
            raise ValueError("Unsupported device view")
        items, warnings = self._facts()
        try:
            labels = self._labels()
            revision, editable = labels.revision, True
        except (OSError, LabelsUnavailable):
            labels = DeviceLabelDocument()
            revision, editable = None, False
            warnings.add(
                "Saved household labels could not be read safely. Label editing is unavailable "
                "until the local label file is recovered; saved scan evidence is unchanged."
            )
        for item in items:
            item["annotations"] = labels.entries.get(
                item["device_key"], DeviceLabels()
            ).model_dump()
            item["editable"] = editable
        if view in {"favourites", "not-recognised"} and not editable:
            raise LabelsUnavailable(
                "This view needs readable household labels. Choose All devices to read saved "
                "observations; recover the labels before using this view."
            )
        if view != "all":
            items = [
                item
                for item in items
                if {
                    "favourites": item["annotations"]["favourite"],
                    "not-recognised": not item["annotations"]["recognised"],
                    "unfinished": item["unfinished_count"] > 0,
                    "review": item["review_count"] > 0,
                }[view]
            ]
        terms = search.casefold().split()
        if terms:
            items = [
                item
                for item in items
                if all(
                    term
                    in " ".join(
                        (
                            item["display_name"],
                            item["last_ip"],
                            item["network"] or "",
                            item["annotations"]["room"],
                        )
                    ).casefold()
                    for term in terms
                )
            ]
        items.sort(
            key=lambda item: (
                not item["annotations"]["favourite"],
                -(
                    observation_time(item["last_observed"])
                    - datetime.min.replace(tzinfo=timezone.utc)
                ).total_seconds()
                if item["last_observed"]
                else float("inf"),
                item["display_name"].casefold(),
                item["device_key"],
            )
        )
        return {
            "items": items[offset : offset + limit],
            "total": len(items),
            "offset": offset,
            "limit": limit,
            "warnings": sorted(warnings),
            "revision": revision,
            "view": view,
        }

    def update(self, device_key: str, update: DeviceLabelUpdate):
        self._safe_paths()
        with self.lock:
            labels = self._labels_locked()
            if labels.revision != update.expected_revision:
                raise LabelRevisionConflict("Household labels changed; reload saved labels first")
            items, _warnings = self._facts()
            if not any(item["device_key"] == device_key for item in items):
                raise UnknownDevice("This device is no longer in the saved inventory")
            entries = dict(labels.entries)
            annotation = DeviceLabels(
                room=update.room, favourite=update.favourite, recognised=update.recognised
            )
            if annotation == DeviceLabels():
                entries.pop(device_key, None)
            else:
                entries[device_key] = annotation
            if len(entries) > MAX_LABEL_ENTRIES:
                raise LabelCapacityExceeded("Household label capacity reached")
            changed = DeviceLabelDocument(revision=labels.revision + 1, entries=entries)
            payload = changed.model_dump_json(indent=2)
            if len(payload.encode("utf-8")) > MAX_LABEL_BYTES:
                raise LabelCapacityExceeded("Household label size limit reached")
            self._safe_paths()
            self.store._atomic_write(self.path, payload, self.backup)
            return {
                "device_key": device_key,
                "annotations": annotation.model_dump(),
                "revision": changed.revision,
                "editable": True,
            }
