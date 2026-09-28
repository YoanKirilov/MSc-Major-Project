from uuid import uuid4

import pytest
from app.main import create_app
from app.schemas.scan import Device, ScanDocument
from app.security.session import SessionManager
from app.storage.json_store import JsonStore
from app.storage.nicknames import NicknameStore, NicknameUpdate
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL, authenticate_client


def document(created="2026-09-26T12:00:00Z"):
    scan_id = str(uuid4())
    return ScanDocument(
        scan_id=scan_id,
        created_at=created,
        state="completed",
        phase="finished",
        target={"mode": "known_hosts", "hosts": ["192.168.0.10"]},
        policy={"allowed_network": "192.168.0.0/24"},
        devices=[
            Device(
                device_id=str(uuid4()),
                scan_id=scan_id,
                ip="192.168.0.10",
                mac="aa:bb:cc:dd:ee:ff",
                hostname="Reported name",
            )
        ],
    )


@pytest.mark.asyncio
async def test_nickname_edit_remove_and_no_evidence_rewrite(tmp_path):
    store = JsonStore(tmp_path)
    original = document()
    await store.create_scan(original)
    evidence = (tmp_path / "scans" / original.scan_id / "scan.json").read_bytes()
    names = NicknameStore(store)
    device_id = original.devices[0].device_id
    revision = await names.update(
        original, device_id, NicknameUpdate(expected_revision=1, nickname="TV")
    )
    assert await names.view(original) == (revision, {device_id: "TV"})
    with pytest.raises(ValueError):
        await names.update(
            original, device_id, NicknameUpdate(expected_revision=1, nickname="stale")
        )
    await names.update(original, device_id, NicknameUpdate(expected_revision=2, nickname="Room TV"))
    await names.update(original, device_id, NicknameUpdate(expected_revision=3, nickname=""))
    assert await names.view(original) == (4, {})
    assert evidence == (tmp_path / "scans" / original.scan_id / "scan.json").read_bytes()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case", ["match", "ip_only", "scope", "duplicate", "source_duplicate", "old", "future"]
)
async def test_reuse_requires_recent_unique_scope_mac(tmp_path, case):
    store = JsonStore(tmp_path)
    original = document()
    current = document("2026-09-27T12:00:00Z")
    if case == "ip_only":
        current.devices[0].mac = None
    elif case == "scope":
        current.policy["allowed_network"] = "192.168.1.0/24"
    elif case == "duplicate":
        current.devices.append(current.devices[0].model_copy(update={"device_id": str(uuid4())}))
    elif case == "old":
        current.created_at = "2026-10-10T12:00:00Z"
    elif case == "source_duplicate":
        original.devices.append(original.devices[0].model_copy(update={"device_id": str(uuid4())}))
    elif case == "future":
        current.created_at = "2026-09-25T12:00:00Z"
    await store.create_scan(original)
    names = NicknameStore(store)
    await names.update(
        original,
        original.devices[0].device_id,
        NicknameUpdate(expected_revision=1, nickname="Room TV"),
    )
    _, labels = await names.view(current)
    assert bool(labels) == (case == "match")


def test_nickname_api_auth_validation_and_corrupt_annotations_do_not_hide_report():
    manager = SessionManager()
    original = document()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        client.portal.call(client.app.state.store.create_scan, original)
        url = f"/api/live-scans/{original.scan_id}/devices/{original.devices[0].device_id}/nickname"
        assert client.put(url, json={"nickname": "TV", "expected_revision": 1}).status_code == 403
        headers = authenticate_client(client, manager)
        assert client.put(url, json={"nickname": "TV", "expected_revision": 1}).status_code == 403
        assert (
            client.put(
                url,
                headers={**headers, "Origin": "https://untrusted.example"},
                json={"nickname": "TV", "expected_revision": 1},
            ).status_code
            == 403
        )
        assert (
            client.put(
                url, headers=headers, json={"nickname": "X" * 81, "expected_revision": 1}
            ).status_code
            == 422
        )
        assert (
            client.put(
                url,
                headers=headers,
                json={"nickname": "<script>TV</script>", "expected_revision": 1},
            ).status_code
            == 200
        )
        result = client.get(f"/api/live-scans/{original.scan_id}").json()
        assert result["devices"][0]["hostname"] == "Reported name"
        assert result["user_nicknames"][original.devices[0].device_id] == "<script>TV</script>"
        client.app.state.store._atomic_write(
            client.app.state.store.data_root / "nicknames.json", "{}BAD"
        )
        result = client.get(f"/api/live-scans/{original.scan_id}")
        assert result.status_code == 200
        assert "nickname_error" in result.json()
