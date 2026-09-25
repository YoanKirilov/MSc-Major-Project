import asyncio
import json
import os

import pytest
from app.schemas.scan import ScanDocument
from app.schemas.settings import Settings, SettingsUpdate
from app.storage import json_store as store_module
from app.storage.json_store import JsonStore


@pytest.mark.parametrize("payload", ["[]", "null", "42", '{"value": NaN}', '{"value": Infinity}'])
def test_managed_json_rejects_wrong_root_and_nonfinite_numbers(temp_store, payload):
    path = temp_store.data_root / "invalid.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError):
        temp_store._read_json(path)


@pytest.mark.parametrize("cache_name", ["progress.json", "summary.json"])
@pytest.mark.parametrize("damage", ["array", "missing_source", "wrong_count", "wrong_nested_type"])
@pytest.mark.asyncio
async def test_invalid_caches_fall_back_to_primary(temp_store, cache_name, damage):
    scan = ScanDocument(
        scan_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        source="demo",
        target={"mode": "demo"},
        state="completed",
        phase="finished",
    )
    await temp_store.create_scan(scan)
    folder = temp_store.data_root / "scans" / scan.scan_id
    cache = folder / cache_name
    data = json.loads(cache.read_text(encoding="utf-8"))
    if damage == "array":
        data = []
    elif damage == "missing_source":
        del data["source"]
    elif damage == "wrong_count":
        data["device_count"] = "not a count"
    elif cache_name == "progress.json":
        data["coverage"]["targets"] = {}
    else:
        data["state"] = {}
    cache.write_text(json.dumps(data), encoding="utf-8")
    future = (folder / "scan.json").stat().st_mtime + 10
    os.utime(cache, (future, future))
    if cache_name == "progress.json":
        result = await temp_store.load_progress(scan.scan_id)
    else:
        result = (await temp_store.list_scans(source="demo", offset=0, limit=20))["items"][0]
        assert result["storage_status"] == "ok"
    assert result["source"] == "demo"
    assert result["device_count"] == 0
    assert result["state"] == "completed"


@pytest.fixture
def temp_store(tmp_path):
    return JsonStore(tmp_path)


def test_atomic_write_retries_short_windows_file_lock(temp_store, monkeypatch):
    target = temp_store.data_root / "retry.json"
    real_replace = store_module.os.replace
    attempts = []

    def temporarily_locked(source, destination):
        attempts.append(1)
        if len(attempts) < 3:
            error = PermissionError(13, "Temporary sharing lock")
            error.winerror = 5
            raise error
        return real_replace(source, destination)

    monkeypatch.setattr(store_module.os, "replace", temporarily_locked)
    monkeypatch.setattr(store_module.time, "sleep", lambda _seconds: None)
    temp_store._atomic_write(target, '{"ok": true}')
    assert target.read_text(encoding="utf-8") == '{"ok": true}'
    assert len(attempts) == 3


def test_oversized_utf8_write_preserves_file_and_backup(temp_store):
    target = temp_store.data_root / "report.json"
    backup = temp_store.data_root / "previous.json"
    temp_store._atomic_write(target, '{"ok":true}')
    temp_store._atomic_write(backup, '{"old":true}')
    temp_store.max_document_bytes = 20
    with pytest.raises(ValueError, match="size limit"):
        temp_store._atomic_write(
            target, json.dumps({"value": "é" * 15}, ensure_ascii=False), backup
        )
    assert temp_store._read_json(target) == {"ok": True}
    assert temp_store._read_json(backup) == {"old": True}


def test_temporary_filenames_are_short_and_exclusively_created(temp_store, monkeypatch):
    real_replace = store_module.os.replace
    seen = []

    def check_replace(source, destination):
        seen.append(source)
        assert len(source.name) < 24
        assert source.parent == destination.parent
        return real_replace(source, destination)

    monkeypatch.setattr(store_module.os, "replace", check_replace)
    target = temp_store.data_root / ("guidance-" + "a" * 36 + ".json")
    temp_store._atomic_write(target, '{"ok":true}')
    assert seen and temp_store._read_json(target)["ok"]


@pytest.mark.asyncio
async def test_invalid_update_does_not_replace_good_report(temp_store):
    scan = ScanDocument(
        scan_id="66666666-6666-4666-8666-666666666666", target={"mode": "demo", "hosts": []}
    )
    saved = await temp_store.create_scan(scan)
    with pytest.raises(ValueError):
        await temp_store.update_scan(
            scan.scan_id, lambda current: current.model_copy(update={"state": "not-a-state"})
        )
    assert (await temp_store.load_scan(scan.scan_id)).model_dump() == saved.model_dump()


def test_failed_replacement_preserves_previous_report_and_backup(temp_store, monkeypatch):
    target = temp_store.data_root / "scan.json"
    backup = temp_store.data_root / "scan.previous.json"
    temp_store._atomic_write(target, '{"old":true}')
    real_replace = store_module.os.replace

    def fail_primary(source, destination):
        if destination == target:
            raise OSError("synthetic disk failure")
        return real_replace(source, destination)

    monkeypatch.setattr(store_module.os, "replace", fail_primary)
    with pytest.raises(OSError):
        temp_store._atomic_write(target, '{"new":true}', backup)
    assert temp_store._read_json(target) == temp_store._read_json(backup) == {"old": True}
    assert not list(temp_store.data_root.glob(".w-*.tmp"))


@pytest.mark.asyncio
async def test_old_guidance_is_split_into_readable_json_archives(temp_store):
    from app.schemas.scan import GuidanceSnapshot

    scan = ScanDocument(
        scan_id="77777777-7777-4777-8777-777777777777",
        target={"mode": "demo", "cidr": None, "hosts": []},
        guidance_history=[
            GuidanceSnapshot(
                saved_at=f"2026-01-0{i}T00:00:00Z", versions={}, findings=[], explanations=[]
            )
            for i in range(1, 6)
        ],
    )
    saved = await temp_store.create_scan(scan)
    assert len(saved.guidance_history) == 3
    assert len(saved.guidance_archives) == 2
    archived = await temp_store.load_guidance_archive(saved.scan_id, saved.guidance_archives[0])
    assert archived["saved_at"] == "2026-01-01T00:00:00Z"
    with pytest.raises(FileNotFoundError):
        await temp_store.load_guidance_archive(saved.scan_id, "../scan.json")


@pytest.mark.asyncio
async def test_settings_round_trip(temp_store):
    settings = Settings(allowed_network="192.168.0.0/24", interface="eth0")
    path = temp_store.data_root / "settings.json"
    path.write_text(
        json.dumps(settings.model_dump(mode="json"), ensure_ascii=False), encoding="utf-8"
    )
    loaded = await temp_store.load_settings()
    assert loaded.allowed_network == "192.168.0.0/24"
    assert loaded.interface == "eth0"


@pytest.mark.asyncio
async def test_settings_update_records_ai_consent_and_revision(temp_store):
    before = await temp_store.load_settings()
    updated = await temp_store.update_settings(
        SettingsUpdate(expected_revision=before.revision, ai_enabled=True),
        before.revision,
    )

    assert updated.ai_enabled is True
    assert updated.ai_consent_revision == before.ai_consent_revision
    assert updated.revision == before.revision + 1
    assert updated.updated_at is not None


@pytest.mark.asyncio
async def test_settings_can_clear_network_and_interface(temp_store):
    initial = await temp_store.update_settings(
        SettingsUpdate(expected_revision=1, allowed_network="192.168.0.0/24", interface="eth6"), 1
    )
    cleared = await temp_store.update_settings(
        SettingsUpdate(expected_revision=initial.revision, allowed_network=None, interface=None),
        initial.revision,
    )
    assert cleared.allowed_network is None
    assert cleared.interface is None


def test_storage_writability_uses_the_scan_lock_directory(temp_store, monkeypatch):
    assert temp_store.storage_writable() is True
    monkeypatch.setattr("app.storage.json_store.FileLock", lambda *args, **kwargs: _DenyLock())
    assert temp_store.storage_writable() is False


class _DenyLock:
    def __enter__(self):
        raise PermissionError("denied")

    def __exit__(self, *_args):
        return False


def test_settings_reject_overly_broad_network_scope():
    with pytest.raises(ValueError, match="/24"):
        Settings(allowed_network="10.0.0.0/8")


def test_settings_reject_null_boolean_updates():
    with pytest.raises(ValueError, match="ai_enabled must be true or false"):
        SettingsUpdate(expected_revision=1, ai_enabled=None)


@pytest.mark.asyncio
async def test_scan_store_can_load_valid_document(temp_store):
    scan = ScanDocument(
        scan_id="11111111-1111-4111-8111-111111111111",
        source="demo",
        target={"mode": "demo", "cidr": None, "hosts": []},
    )
    path = temp_store.data_root / "scans" / scan.scan_id
    path.mkdir(parents=True, exist_ok=True)
    path.joinpath("scan.json").write_text(
        json.dumps(scan.model_dump(mode="json"), ensure_ascii=False), encoding="utf-8"
    )
    loaded = await temp_store.load_scan(scan.scan_id)
    assert loaded.scan_id == scan.scan_id
    assert loaded.source == "demo"


@pytest.mark.asyncio
async def test_update_keeps_previous_revision_and_rejects_stale_revision(temp_store):
    scan = ScanDocument(
        scan_id="22222222-2222-4222-8222-222222222222",
        source="demo",
        target={"mode": "demo", "cidr": None, "hosts": []},
    )
    await temp_store.create_scan(scan)
    updated = await temp_store.update_scan(
        scan.scan_id,
        lambda current: current.model_copy(update={"state": "completed"}),
        expected_revision=1,
    )
    assert updated.revision == 2
    assert (temp_store.data_root / "scans" / scan.scan_id / "scan.previous.json").exists()
    with pytest.raises(ValueError, match="revision conflict"):
        await temp_store.update_scan(scan.scan_id, lambda current: current, expected_revision=1)


@pytest.mark.asyncio
async def test_duplicate_json_keys_are_rejected(temp_store):
    scan_id = "33333333-3333-4333-8333-333333333333"
    path = temp_store.data_root / "scans" / scan_id
    path.mkdir(parents=True)
    path.joinpath("scan.json").write_text(
        '{"schema_version": 1, "schema_version": 1}', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="duplicate"):
        await temp_store.load_scan(scan_id)


@pytest.mark.asyncio
async def test_corrupt_scan_is_visible_in_history(temp_store):
    scan_id = "44444444-4444-4444-8444-444444444444"
    path = temp_store.data_root / "scans" / scan_id
    path.mkdir(parents=True)
    path.joinpath("scan.json").write_text("not json", encoding="utf-8")
    history = await temp_store.list_scans(source=None, offset=0, limit=20)
    assert history["items"][0]["storage_status"] == "unreadable"


@pytest.mark.asyncio
async def test_history_uses_creation_time_not_random_uuid_order(temp_store):
    older = ScanDocument(
        scan_id="ffffffff-ffff-4fff-8fff-ffffffffffff",
        source="demo",
        target={"mode": "demo", "cidr": None, "hosts": []},
        created_at="2020-01-01T00:00:00Z",
    )
    newer = ScanDocument(
        scan_id="11111111-1111-4111-8111-111111111111",
        source="demo",
        target={"mode": "demo", "cidr": None, "hosts": []},
        created_at="2021-01-01T00:00:00Z",
    )
    await temp_store.create_scan(older)
    await temp_store.create_scan(newer)
    history = await temp_store.list_scans(source="demo", offset=0, limit=20)
    assert [item["scan_id"] for item in history["items"]] == [newer.scan_id, older.scan_id]


@pytest.mark.asyncio
async def test_history_reads_small_json_summary_when_current(temp_store, monkeypatch):
    scan = ScanDocument(
        scan_id="abababab-abab-4aba-8aba-abababababab",
        source="demo",
        target={"mode": "demo", "cidr": None, "hosts": []},
    )
    await temp_store.create_scan(scan)
    assert (temp_store.data_root / "scans" / scan.scan_id / "summary.json").exists()
    original_read = temp_store._read_json

    def read_only_summary(path):
        if path.name == "scan.json":
            raise AssertionError("history should use the current small summary")
        return original_read(path)

    monkeypatch.setattr(temp_store, "_read_json", read_only_summary)
    history = await temp_store.list_scans(source="demo", offset=0, limit=20)
    assert history["items"][0]["scan_id"] == scan.scan_id


@pytest.mark.asyncio
async def test_concurrent_scan_updates_are_serialized(temp_store):
    scan = ScanDocument(
        scan_id="55555555-5555-4555-8555-555555555555",
        source="demo",
        target={"mode": "demo", "cidr": None, "hosts": []},
    )
    await temp_store.create_scan(scan)

    def add_warning(code):
        def mutate(current):
            return current.model_copy(
                update={
                    "warnings": [*current.warnings, {"code": code, "message": code}],
                }
            )

        return mutate

    await asyncio.gather(
        temp_store.update_scan(scan.scan_id, add_warning("FIRST")),
        temp_store.update_scan(scan.scan_id, add_warning("SECOND")),
    )

    saved = await temp_store.load_scan(scan.scan_id)
    assert saved.revision == 3
    assert {warning["code"] for warning in saved.warnings} == {"FIRST", "SECOND"}
    scan_dir = temp_store.data_root / "scans" / scan.scan_id
    assert not list(scan_dir.glob("*.tmp"))


@pytest.mark.asyncio
async def test_raw_output_is_bounded_and_uses_managed_names(temp_store):
    scan = ScanDocument(
        scan_id="99999999-9999-4999-8999-999999999998",
        source="demo",
        target={"mode": "demo", "cidr": None, "hosts": []},
    )
    await temp_store.create_scan(scan)

    await temp_store.save_raw_output(scan.scan_id, "host-192-168-0-2.xml", b"<nmaprun />")

    path = temp_store.data_root / "scans" / scan.scan_id / "raw" / "host-192-168-0-2.xml"
    assert path.read_bytes() == b"<nmaprun />"
    with pytest.raises(ValueError, match="invalid raw output name"):
        await temp_store.save_raw_output(scan.scan_id, "../outside.xml", b"unsafe")
