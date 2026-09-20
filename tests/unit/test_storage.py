import asyncio
import json

import pytest

from app.schemas.scan import ScanDocument
from app.schemas.settings import Settings
from app.storage.json_store import JsonStore


@pytest.fixture
def temp_store(tmp_path):
    return JsonStore(tmp_path)


@pytest.mark.asyncio
async def test_settings_round_trip(temp_store):
    settings = Settings(allowed_network="192.168.0.0/24", interface="eth0")
    path = temp_store.data_root / "settings.json"
    path.write_text(json.dumps(settings.model_dump(mode="json"), ensure_ascii=False), encoding="utf-8")
    loaded = await temp_store.load_settings()
    assert loaded.allowed_network == "192.168.0.0/24"
    assert loaded.interface == "eth0"


@pytest.mark.asyncio
async def test_scan_store_can_load_valid_document(temp_store):
    scan = ScanDocument(scan_id="11111111-1111-4111-8111-111111111111", source="demo", target={"mode": "demo", "cidr": None, "hosts": []})
    path = temp_store.data_root / "scans" / scan.scan_id
    path.mkdir(parents=True, exist_ok=True)
    path.joinpath("scan.json").write_text(json.dumps(scan.model_dump(mode="json"), ensure_ascii=False), encoding="utf-8")
    loaded = await temp_store.load_scan(scan.scan_id)
    assert loaded.scan_id == scan.scan_id
    assert loaded.source == "demo"


@pytest.mark.asyncio
async def test_update_keeps_previous_revision_and_rejects_stale_revision(temp_store):
    scan = ScanDocument(scan_id="22222222-2222-4222-8222-222222222222", source="demo", target={"mode": "demo", "cidr": None, "hosts": []})
    await temp_store.create_scan(scan)
    updated = await temp_store.update_scan(scan.scan_id, lambda current: current.model_copy(update={"state": "completed"}), expected_revision=1)
    assert updated.revision == 2
    assert (temp_store.data_root / "scans" / scan.scan_id / "scan.previous.json").exists()
    with pytest.raises(ValueError, match="revision conflict"):
        await temp_store.update_scan(scan.scan_id, lambda current: current, expected_revision=1)


@pytest.mark.asyncio
async def test_duplicate_json_keys_are_rejected(temp_store):
    scan_id = "33333333-3333-4333-8333-333333333333"
    path = temp_store.data_root / "scans" / scan_id
    path.mkdir(parents=True)
    path.joinpath("scan.json").write_text('{"schema_version": 1, "schema_version": 1}', encoding="utf-8")
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
