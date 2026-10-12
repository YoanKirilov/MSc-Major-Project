"""User annotations kept separately from immutable scanner observations."""

import asyncio
import shutil
from datetime import timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.scanner.names import normalise_mac
from app.schemas.common import StrictModel, observation_time
from filelock import FileLock
from pydantic import Field, field_validator

from .recovery import reserve_recovery_revision


class NicknameUpdate(StrictModel):
    expected_revision: int = Field(ge=1)
    nickname: str = Field(max_length=80)

    @field_validator("nickname")
    @classmethod
    def clean(cls, value):
        if any(not c.isprintable() for c in value):
            raise ValueError("Use a single line for the nickname")
        return value.strip()


class NicknameEntry(StrictModel):
    scan_id: UUID
    device_id: UUID
    nickname: str = Field(min_length=1, max_length=80)


class NicknameDocument(StrictModel):
    revision: int = Field(default=1, ge=1)
    entries: list[NicknameEntry] = Field(default_factory=list, max_length=200)
    recovery_notice: str | None = Field(default=None, max_length=300)


def matches(current, device, source, original):
    if source.scan_id == current.scan_id:
        return original.device_id == device.device_id
    scope = current.policy.get("allowed_network")
    mac = normalise_mac(device.mac)
    if not scope or source.policy.get("allowed_network") != scope:
        return False
    if not mac or mac == "00:00:00:00:00:00" or normalise_mac(original.mac) != mac:
        return False
    # Reuse only a recent, earlier same-scope observation, never an IP association.
    now, then = observation_time(current.created_at), observation_time(source.created_at)
    if now is None or then is None:
        return False
    age = now - then
    return (
        timedelta(0) <= age <= timedelta(days=7)
        and source.phase == "finished"
        and sum(normalise_mac(d.mac) == mac for d in source.devices) == 1
        and sum(normalise_mac(d.mac) == mac for d in current.devices) == 1
    )


class NicknameStore:
    def __init__(self, store):
        self.store = store
        self.path = store.data_root / "nicknames.json"
        self.lock = FileLock(str(store.data_root / "nicknames.lock"), timeout=5)

    def _load(self):
        with self.lock:
            return self._load_locked()

    def _load_locked(self):
        backup = self.path.with_name("nicknames.previous.json")
        fence = self.path.with_name("nicknames.recovery.json")
        if self.path.is_symlink() or (self.path.exists() and not self.path.is_file()):
            raise ValueError("Refusing to replace an unsafe nicknames path")
        if self.path.exists() and self.path.stat().st_size > self.store.max_document_bytes:
            raise ValueError("Oversized nicknames require manual recovery")
        if (
            not self.path.exists()
            and not backup.exists()
            and not backup.is_symlink()
            and not fence.exists()
            and not fence.is_symlink()
        ):
            return NicknameDocument()
        try:
            return NicknameDocument.model_validate(self.store._read_json(self.path))
        except ValueError:
            saved = NicknameDocument.model_validate(self.store._read_json(backup))
            # The lost primary normally had backup revision + 1. Invalidate that editor too.
            recovered = saved.model_copy(
                update={
                    "recovery_notice": (
                        "Device nicknames were recovered from the previous backup. The latest "
                        "edits may be missing; original scan results are unchanged."
                    ),
                }
            )
            if (
                self.path.exists()
                and len(list(self.path.parent.glob("nicknames.corrupt-*.json"))) >= 5
            ):
                raise ValueError(
                    "Nickname quarantine limit reached; manual recovery required"
                ) from None
            recovered.revision = reserve_recovery_revision(self.store, self.path, saved.revision)
            if self.path.exists():
                shutil.copy2(
                    self.path, self.path.with_name(f"nicknames.corrupt-{uuid4().hex}.json")
                )
            # Do not overwrite the valid backup with corrupt primary bytes.
            self.store._atomic_write(self.path, recovered.model_dump_json(indent=2))
            return recovered

    def _matching(self, entries, document, device, sources=None):
        sources = {} if sources is None else sources
        exact = [
            e
            for e in entries
            if str(e.scan_id) == document.scan_id and str(e.device_id) == device.device_id
        ]
        if exact:
            return exact
        result = []
        for entry in entries:
            try:
                if entry.scan_id not in sources:
                    saved = self.store._load_scan(entry.scan_id)
                    # Read each anchor once per request and retain only identity facts.
                    sources[entry.scan_id] = SimpleNamespace(
                        scan_id=saved.scan_id,
                        created_at=saved.created_at,
                        policy=saved.policy,
                        phase=saved.phase,
                        devices=[
                            SimpleNamespace(device_id=d.device_id, mac=d.mac) for d in saved.devices
                        ],
                    )
                source = sources[entry.scan_id]
                original = next(d for d in source.devices if d.device_id == str(entry.device_id))
                if matches(document, device, source, original):
                    result.append(entry)
            except (OSError, ValueError, TypeError, StopIteration):
                continue
        # Several plausible identities are ambiguous, even when their labels agree.
        return result if len(result) == 1 else []

    def _view(self, document, saved=None):
        saved = self._load() if saved is None else saved
        names = {}
        sources = {}
        for device in document.devices:
            entries = self._matching(saved.entries, document, device, sources)
            if entries:
                names[device.device_id] = entries[0].nickname
        return saved.revision, names

    async def view(self, document):
        return await asyncio.to_thread(self._view, document)

    def _snapshot(self, document, known_revision):
        saved = self._load()
        result = {"revision": saved.revision}
        if saved.recovery_notice:
            result["recovery_notice"] = saved.recovery_notice
        if known_revision == saved.revision:
            return {**result, "changed": False}
        revision, names = self._view(document, saved)
        return {**result, "revision": revision, "changed": True, "names": names}

    async def snapshot(self, document, known_revision=None):
        return await asyncio.to_thread(self._snapshot, document, known_revision)

    def _update(self, document, device_id, update):
        device = next((d for d in document.devices if d.device_id == device_id), None)
        if device is None:
            raise FileNotFoundError("Device not found")
        with self.lock:
            saved = self._load_locked()
            if saved.revision != update.expected_revision:
                raise ValueError("Nicknames changed; reload this report before saving")
            matched = self._matching(saved.entries, document, device)
            entries = [e for e in saved.entries if e not in matched]
            if update.nickname:
                # Editing a reused nickname keeps its original identity anchor and age.
                entries.append(
                    NicknameEntry(
                        scan_id=matched[0].scan_id if matched else document.scan_id,
                        device_id=matched[0].device_id if matched else device.device_id,
                        nickname=update.nickname,
                    )
                )
            changed = NicknameDocument(
                revision=saved.revision + 1, entries=entries, recovery_notice=saved.recovery_notice
            )
            self.store._atomic_write(
                self.path,
                changed.model_dump_json(indent=2),
                self.path.with_name("nicknames.previous.json"),
            )
            return changed.revision

    async def update(self, document, device_id, update):
        return await asyncio.to_thread(self._update, document, device_id, update)
