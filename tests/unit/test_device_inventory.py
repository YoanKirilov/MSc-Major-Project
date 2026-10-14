import json
from uuid import uuid4

import pytest
from app.main import create_app
from app.schemas.scan import Coverage, Device, ScanDocument, TargetLedgerEntry
from app.security.session import SessionManager
from app.storage import device_inventory as inventory_module
from app.storage.backup import transfer
from app.storage.device_inventory import (
    DeviceInventory,
    DeviceLabelUpdate,
    LabelRevisionConflict,
    LabelsUnavailable,
    UnknownDevice,
)
from app.storage.json_store import JsonStore
from app.storage.nicknames import NicknameStore, NicknameUpdate
from fastapi.testclient import TestClient
from pydantic import ValidationError
from tests.session_helpers import BASE_URL, authenticate_client


def document(
    *,
    created="2026-10-12T12:00:00Z",
    ip="192.168.0.10",
    mac="aa:bb:cc:dd:ee:02",
    network="192.168.0.0/24",
    state="completed",
    phase="finished",
    source="live",
):
    scan_id = str(uuid4())
    return ScanDocument(
        scan_id=scan_id,
        created_at=created,
        state=state,
        phase=phase,
        source=source,
        target={"mode": "known_hosts", "hosts": [ip]},
        policy={"allowed_network": network},
        devices=[
            Device(
                scan_id=scan_id,
                device_id=str(uuid4()),
                ip=ip,
                mac=mac,
                hostname="Reported device",
                observed_at=created,
            )
        ],
        coverage=Coverage(
            candidate_count=1,
            service_completed_count=int(state == "completed"),
            service_stage_complete=state == "completed",
            targets=[
                TargetLedgerEntry(
                    ip=ip,
                    service_status="completed" if state == "completed" else "timed_out",
                )
            ],
        ),
    )


def save(store, doc):
    return store._create_scan(doc)


def test_inventory_groups_only_unique_mac_with_same_valid_network(tmp_path):
    store = JsonStore(tmp_path)
    first = save(store, document())
    save(
        store, document(created="2026-10-13T12:00:00Z", ip="192.168.0.15", mac="AA-BB-CC-DD-EE-02")
    )
    save(store, document(ip="192.168.1.10", network="192.168.1.0/24"))
    missing = save(store, document(mac=None))
    save(store, document(mac=None))
    duplicate = document()
    duplicate.devices.append(duplicate.devices[0].model_copy(update={"device_id": str(uuid4())}))
    save(store, duplicate)
    inventory = DeviceInventory(store).list()
    assert inventory["total"] == 6
    matched = next(item for item in inventory["items"] if item["report_count"] == 2)
    assert matched["last_ip"] == "192.168.0.15"
    assert matched["first_observed"] == first.created_at
    assert matched["last_observed"] == "2026-10-13T12:00:00Z"
    assert matched["network"] == "192.168.0.0/24"
    missing_item = next(
        item for item in inventory["items"] if item["reports"][0]["scan_id"] == missing.scan_id
    )
    assert missing_item["report_count"] == 1
    assert matched["unfinished_count"] == 0


@pytest.mark.parametrize(
    "mac", [None, "00:00:00:00:00:00", "ff:ff:ff:ff:ff:ff", "01:bb:cc:dd:ee:02", "bad"]
)
def test_inventory_never_reuses_unusable_mac(tmp_path, mac):
    store = JsonStore(tmp_path)
    save(store, document(mac=mac))
    save(store, document(mac=mac))
    assert DeviceInventory(store).list()["total"] == 2


@pytest.mark.parametrize(
    "network,ip",
    [(None, "192.168.0.10"), ("192.168.0.0/24", "192.168.1.10"), ("127.0.0.0/8", "127.0.0.10")],
)
def test_inventory_never_reuses_mac_without_valid_scope(tmp_path, network, ip):
    store = JsonStore(tmp_path)
    save(store, document(network=network, ip=ip))
    save(store, document(network=network, ip=ip))
    assert DeviceInventory(store).list()["total"] == 2


def test_inventory_uses_only_finished_live_reports_and_saved_dates(tmp_path):
    store = JsonStore(tmp_path)
    live = save(store, document(state="partial"))
    save(store, document(source="demo", mac="aa:bb:cc:dd:ee:04"))
    save(store, document(state="running", phase="service_scan", mac="aa:bb:cc:dd:ee:06"))
    save(store, document(state="queued", phase="queued", mac="aa:bb:cc:dd:ee:08"))
    result = DeviceInventory(store).list()
    assert result["total"] == 1
    item = result["items"][0]
    assert item["reports"][0]["scan_id"] == live.scan_id
    assert item["unfinished_count"] == 1
    assert item["last_observed"] == live.devices[0].observed_at
    assert "online" not in json.dumps(result).casefold()


@pytest.mark.parametrize("discovered", [True, False])
def test_unfinished_target_without_usable_device_stays_visible(tmp_path, discovered):
    store = JsonStore(tmp_path)
    doc = document(state="failed", created="2026-10-10T12:00:00Z")
    doc.devices = []
    target = doc.coverage.targets[0]
    if discovered:
        doc.target = {"mode": "discover", "cidr": "192.168.0.0/24"}
        target.discovery_status = "observed"
        target.discovery_hostname = "Discovery printer"
        target.discovery_mac = "aa:bb:cc:dd:ee:02"
    save(store, doc)
    result = DeviceInventory(store).list()
    assert result["total"] == 1
    item = result["items"][0]
    assert item["last_ip"] == target.ip
    assert item["unfinished_count"] == 1
    assert item["review_count"] == 0
    assert item["first_observed"] == item["last_observed"] == doc.created_at
    assert item["reports"] == [
        {
            "scan_id": doc.scan_id,
            "device_id": None,
            "created_at": doc.created_at,
            "state": "failed",
        }
    ]
    assert "device checks did not finish" in item["identity_note"]
    assert item["display_name"] == ("Discovery printer" if discovered else "Unnamed device")


def test_unobserved_discovery_addresses_are_not_inventory_devices(tmp_path):
    store = JsonStore(tmp_path)
    doc = document(state="failed")
    doc.devices = []
    doc.target = {"mode": "discover", "cidr": "192.168.0.0/24"}
    doc.coverage.targets[0].discovery_status = "not_seen"
    save(store, doc)
    assert DeviceInventory(store).list()["total"] == 0


def test_discovery_only_mac_duplicate_prevents_completed_device_merge(tmp_path):
    store = JsonStore(tmp_path)
    ambiguous = document()
    ambiguous.coverage.targets.append(
        TargetLedgerEntry(
            ip="192.168.0.20",
            discovery_status="observed",
            service_status="failed",
            discovery_mac=ambiguous.devices[0].mac,
        )
    )
    save(store, ambiguous)
    save(store, document(created="2026-10-13T12:00:00Z"))
    items = DeviceInventory(store).list()["items"]
    assert len(items) == 3
    assert all(item["report_count"] == 1 for item in items)
    assert sum("identity_note" in item for item in items) == 1


def test_label_revision_backup_and_evidence_preservation(tmp_path):
    store = JsonStore(tmp_path)
    doc = save(store, document())
    evidence_path = store._scan_dir(doc.scan_id) / "scan.json"
    before = evidence_path.read_bytes()
    inventory = DeviceInventory(store)
    key = inventory.list()["items"][0]["device_key"]
    result = inventory.update(
        key,
        DeviceLabelUpdate(
            expected_revision=1,
            room=" Living room ",
            favourite=True,
            recognised=True,
        ),
    )
    assert result["revision"] == 2
    assert result["annotations"]["room"] == "Living room"
    with pytest.raises(LabelRevisionConflict):
        inventory.update(key, DeviceLabelUpdate(expected_revision=1, room="Stale"))
    inventory.update(key, DeviceLabelUpdate(expected_revision=2, room="Bedroom"))
    assert json.loads(inventory.backup.read_text())["revision"] == 2
    assert inventory.list()["items"][0]["annotations"]["room"] == "Bedroom"
    assert evidence_path.read_bytes() == before
    inventory.update(key, DeviceLabelUpdate(expected_revision=3))
    assert json.loads(inventory.path.read_text())["entries"] == {}


@pytest.mark.parametrize(
    "payload",
    [
        "{broken",
        '{"revision":true,"entries":{}}',
        '{"revision":1,"entries":{},"extra":1}',
        '{"revision":1,"revision":2,"entries":{}}',
        '{"revision":1,"entries":{"../outside":{"room":"x"}}}',
    ],
)
def test_unreadable_metadata_is_visible_and_edit_fails_closed(tmp_path, payload):
    store = JsonStore(tmp_path)
    save(store, document())
    inventory = DeviceInventory(store)
    key = inventory.list()["items"][0]["device_key"]
    store._atomic_write(inventory.path, payload)
    store._atomic_write(inventory.backup, '{"revision":1,"entries":{}}')
    before = inventory.path.read_bytes()
    result = inventory.list()
    assert result["revision"] is None
    assert result["items"][0]["editable"] is False
    assert any("could not be read" in warning for warning in result["warnings"])
    with pytest.raises(LabelsUnavailable):
        inventory.update(key, DeviceLabelUpdate(expected_revision=1, room="New"))
    assert inventory.path.read_bytes() == before


def test_missing_primary_with_backup_does_not_reset_revision(tmp_path):
    store = JsonStore(tmp_path)
    save(store, document())
    inventory = DeviceInventory(store)
    store._atomic_write(inventory.backup, '{"revision":5,"entries":{}}')
    assert inventory.list()["revision"] is None
    assert not inventory.path.exists()


def test_inventory_metadata_path_cannot_be_directory(tmp_path):
    store = JsonStore(tmp_path)
    save(store, document())
    inventory = DeviceInventory(store)
    inventory.path.mkdir()
    assert inventory.list()["revision"] is None
    with pytest.raises(LabelsUnavailable):
        inventory.update("d-" + "0" * 64, DeviceLabelUpdate(expected_revision=1))


def test_nickname_search_pagination_and_favourite_order(tmp_path):
    store = JsonStore(tmp_path)
    old = save(store, document())
    new = save(store, document(created="2026-10-13T12:00:00Z", mac="aa:bb:cc:dd:ee:04"))
    NicknameStore(store)._update(
        old, old.devices[0].device_id, NicknameUpdate(expected_revision=1, nickname="Living TV")
    )
    inventory = DeviceInventory(store)
    found = inventory.list(search="living tv")["items"]
    assert len(found) == 1
    assert found[0]["display_name"] == "Living TV"
    inventory.update(
        found[0]["device_key"],
        DeviceLabelUpdate(
            expected_revision=1,
            room="Lounge",
            favourite=True,
        ),
    )
    assert inventory.list(limit=1)["items"][0]["reports"][0]["scan_id"] == old.scan_id
    assert inventory.list(offset=1, limit=1)["items"][0]["reports"][0]["scan_id"] == new.scan_id
    assert inventory.list(search="lounge")["total"] == 1


def test_bounded_reports_and_links_show_limits(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    for day in range(10, 14):
        save(store, document(created=f"2026-10-{day}T12:00:00Z"))
    monkeypatch.setattr(inventory_module, "MAX_REPORTS", 3)
    monkeypatch.setattr(inventory_module, "MAX_REPORT_LINKS", 2)
    loads = []
    original_load = store._load_scan

    def counted(scan_id):
        loads.append(scan_id)
        return original_load(scan_id)

    monkeypatch.setattr(store, "_load_scan", counted)
    result = DeviceInventory(store).list()
    assert len(loads) == 3
    assert result["items"][0]["report_count"] == 3
    assert len(result["items"][0]["reports"]) == 2
    assert result["items"][0]["first_observed"] == "2026-10-11T12:00:00Z"
    assert len(result["warnings"]) == 2


def test_unknown_device_cannot_create_metadata(tmp_path):
    inventory = DeviceInventory(JsonStore(tmp_path))
    with pytest.raises(UnknownDevice):
        inventory.update("d-" + "0" * 64, DeviceLabelUpdate(expected_revision=1, room="New"))
    assert not inventory.path.exists()


def test_inventory_limits_document_bytes_device_observations_and_directory_reads(
    tmp_path,
    monkeypatch,
):
    store = JsonStore(tmp_path)
    first = document()
    first.devices.append(
        first.devices[0].model_copy(
            update={
                "device_id": str(uuid4()),
                "mac": None,
            }
        )
    )
    save(store, first)
    save(store, document(created="2026-10-11T12:00:00Z"))
    monkeypatch.setattr(inventory_module, "MAX_DEVICE_OBSERVATIONS", 1)
    result = DeviceInventory(store).list()
    assert result["total"] == 1
    assert any("observation limit" in warning for warning in result["warnings"])
    monkeypatch.setattr(inventory_module, "MAX_DEVICE_OBSERVATIONS", 4096)
    monkeypatch.setattr(inventory_module, "MAX_EVIDENCE_BYTES", 1)
    result = DeviceInventory(store).list()
    assert result["total"] == 0
    assert any("report read limit" in warning for warning in result["warnings"])
    monkeypatch.setattr(inventory_module, "MAX_EVIDENCE_BYTES", 64 * 1024 * 1024)
    monkeypatch.setattr(inventory_module, "MAX_DIRECTORY_ENTRIES", 1)
    result = DeviceInventory(store).list()
    assert result["items"][0]["report_count"] == 1
    assert any("folder limit" in warning for warning in result["warnings"])


def test_household_labels_and_previous_backup_survive_private_backup_restore(tmp_path):
    source = tmp_path / "source"
    store = JsonStore(source)
    save(store, document())
    inventory = DeviceInventory(store)
    key = inventory.list()["items"][0]["device_key"]
    inventory.update(key, DeviceLabelUpdate(expected_revision=1, room="Bedroom"))
    inventory.update(key, DeviceLabelUpdate(expected_revision=2, room="Office", favourite=True))
    previous = inventory.backup.read_bytes()
    backup, restored = tmp_path / "backup", tmp_path / "restored"
    assert transfer(source, backup)["verified"] is True
    assert (backup / inventory.path.name).read_bytes() == inventory.path.read_bytes()
    assert (backup / inventory.backup.name).read_bytes() == previous
    assert transfer(backup, restored, restore=True)["verified"] is True
    recovered = DeviceInventory(JsonStore(restored)).list()
    assert recovered["revision"] == 3
    assert recovered["items"][0]["annotations"] == {
        "room": "Office",
        "favourite": True,
        "recognised": False,
    }
    assert not (backup / "device-labels.lock").exists()


def test_redirected_labels_paths_fail_closed_without_following(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    save(store, document())
    inventory = DeviceInventory(store)
    path_class = type(inventory.path)
    original = getattr(path_class, "is_junction", lambda path: False)

    def redirected(path):
        return path == inventory.path or original(path)

    monkeypatch.setattr(path_class, "is_junction", redirected, raising=False)
    result = inventory.list()
    assert result["revision"] is None
    assert result["items"][0]["editable"] is False
    with pytest.raises(LabelsUnavailable):
        inventory.update(
            result["items"][0]["device_key"],
            DeviceLabelUpdate(
                expected_revision=1,
                room="Office",
            ),
        )
    assert not inventory.path.exists()


@pytest.mark.parametrize(
    "value",
    [
        {"room": "line\nbreak"},
        {"room": "x" * 81},
        {"favourite": "true"},
        {"recognised": 1},
        {"expected_revision": True},
        {"unexpected": "value"},
    ],
)
def test_labels_validate_bounded_strict_metadata(value):
    with pytest.raises(ValidationError):
        DeviceLabelUpdate.model_validate({"expected_revision": 1, **value})


def test_devices_api_requires_session_csrf_and_rejects_stale_edits():
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        save(client.app.state.store, document())
        assert client.get("/api/devices").status_code == 401
        headers = authenticate_client(client, manager)
        result = client.get("/api/devices").json()
        key = result["items"][0]["device_key"]
        url = f"/api/devices/{key}"
        update = {"expected_revision": 1, "room": "Office", "recognised": True}
        assert client.put(url, json=update).status_code == 403
        assert (
            client.put(
                url,
                json=update,
                headers={
                    **headers,
                    "Origin": "https://untrusted.example",
                },
            ).status_code
            == 403
        )
        response = client.put(url, json=update, headers=headers)
        assert response.status_code == 200
        assert response.json()["revision"] == 2
        assert client.put(url, json=update, headers=headers).status_code == 409
        assert client.get("/api/devices?limit=101").status_code == 422
        assert client.get("/api/devices?offset=-1").status_code == 422
        assert client.get("/api/devices?view=invalid").status_code == 422
        filtered = client.get("/api/devices?view=not-recognised").json()
        assert filtered["total"] == 0 and filtered["view"] == "not-recognised"
        assert client.put("/api/devices/not-a-key", json=update, headers=headers).status_code == 422
        assert (
            client.put(
                "/api/devices/d-" + "0" * 64,
                json={**update, "expected_revision": 2},
                headers=headers,
            ).status_code
            == 404
        )
        assert (
            client.put(
                url, json={**update, "expected_revision": 2, "favourite": "yes"}, headers=headers
            ).status_code
            == 422
        )
        labels = client.app.state.store.data_root / "device-labels.json"
        client.app.state.store._atomic_write(labels, "{broken")
        unreadable = client.get("/api/devices").json()
        assert unreadable["revision"] is None
        assert unreadable["items"][0]["editable"] is False
        for view in ("favourites", "not-recognised"):
            unavailable = client.get(f"/api/devices?view={view}")
            assert unavailable.status_code == 503
            assert "Choose All devices" in unavailable.json()["detail"]
        assert (
            client.put(url, json={**update, "expected_revision": 2}, headers=headers).status_code
            == 503
        )
        assert labels.read_text() == "{broken"


def test_device_views_filter_whole_inventory_before_search_and_paging(tmp_path, monkeypatch):
    inventory = DeviceInventory(JsonStore(tmp_path))
    facts = [
        {
            "device_key": f"d-{index:064x}",
            "display_name": f"Device {index}",
            "last_ip": f"192.168.56.{index}",
            "network": "192.168.56.0/24",
            "last_observed": "2026-10-14T00:00:00Z",
            "unfinished_count": int(index == 29),
            "review_count": int(index == 30),
        }
        for index in range(1, 31)
    ]
    monkeypatch.setattr(inventory, "_facts", lambda: (facts, set()))
    entries = {
        item["device_key"]: {"room": "Study", "favourite": True, "recognised": index < 28}
        for index, item in enumerate(facts)
    }
    inventory.store._atomic_write(inventory.path, json.dumps({"revision": 1, "entries": entries}))
    result = inventory.list(view="favourites", offset=24, search="Study")
    assert result["view"] == "favourites" and result["total"] == 30
    assert len(result["items"]) == 6
    assert inventory.list(view="not-recognised")["total"] == 2
    assert inventory.list(view="unfinished")["items"][0]["display_name"] == "Device 29"
    assert inventory.list(view="review")["items"][0]["display_name"] == "Device 30"
    assert inventory.list(view="unfinished", search="Device 30")["total"] == 0
    with pytest.raises(ValueError, match="Unsupported device view"):
        inventory.list(view="invented")
