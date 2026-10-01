from datetime import timedelta
from uuid import uuid4

import pytest
from app.main import create_app
from app.scanner.name_refresh import lookup_names
from app.schemas.common import iso_z, utc_now
from app.schemas.scan import Device, ScanDocument
from app.security.session import SessionManager
from app.storage.annotations import AnnotationStore, NameRefresh, TitleUpdate
from app.storage.json_store import JsonStore
from app.storage.library import search_reports
from app.storage.library_cache import LibraryCache
from app.storage.nicknames import NicknameStore, NicknameUpdate
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL, authenticate_client


def report(*, days=0, profile="light", scope="192.168.0.0/24", hostname="Example"):
    scan_id = str(uuid4())
    created = iso_z(utc_now() - timedelta(days=days))
    return ScanDocument(
        scan_id=scan_id,
        created_at=created,
        state="completed",
        phase="finished",
        target={"mode": "known_hosts", "hosts": ["192.168.0.10"]},
        policy={"profile": profile, "allowed_network": scope},
        devices=[
            Device(
                device_id=str(uuid4()),
                scan_id=scan_id,
                ip="192.168.0.10",
                hostname=hostname,
                observed_at=created,
            )
        ],
    )


def test_titles_and_refresh_merge_without_changing_scan_evidence(tmp_path):
    store = JsonStore(tmp_path)
    doc = report()
    store._create_scan(doc)
    primary = store._scan_dir(doc.scan_id) / "scan.json"
    original = primary.read_bytes()
    annotation = AnnotationStore(store)
    annotation._update(doc.scan_id, title=TitleUpdate(expected_revision=1, title="My review"))
    annotation._update(
        doc.scan_id,
        refresh=NameRefresh(device_id=doc.devices[0].device_id, checked_at=iso_z(utc_now())),
    )
    assert annotation._load(doc.scan_id).title == "My review"
    assert annotation._load(doc.scan_id).revision == 3
    with pytest.raises(ValueError):
        annotation._update(doc.scan_id, title=TitleUpdate(expected_revision=1, title="stale"))
    assert primary.read_bytes() == original


def test_history_search_precedes_pagination_and_includes_nicknames(tmp_path):
    store = JsonStore(tmp_path)
    for _ in range(23):
        store._create_scan(report())
    wanted = report(days=2, hostname="Old device")
    store._create_scan(wanted)
    NicknameStore(store)._update(
        wanted,
        wanted.devices[0].device_id,
        NicknameUpdate(expected_revision=1, nickname="Kitchen TV"),
    )
    AnnotationStore(store)._update(
        wanted.scan_id, title=TitleUpdate(expected_revision=1, title="Router update")
    )
    for query in ("TV kitchen", "update router", "OLD device"):
        page = search_reports(store, q=query, limit=1)
        assert page["total"] == 1
        assert page["items"][0]["scan_id"] == wanted.scan_id
    assert search_reports(store, profile="deep-tcp-v1")["total"] == 0
    assert search_reports(store, after=utc_now().date())["total"] == 23


def test_picker_only_recent_finished_light_same_scope(tmp_path):
    store = JsonStore(tmp_path)
    wanted = report(days=1)
    for doc in (
        report(days=9),
        report(profile="deep-tcp-v1"),
        report(scope="192.168.1.0/24"),
        wanted,
    ):
        store._create_scan(doc)
    page = search_reports(store, profile="light", scope="192.168.0.0/24", recent_devices=True)
    assert len(page["items"]) == 1
    assert page["items"][0]["scan_id"] == wanted.scan_id
    assert page["items"][0]["observed_at"] == wanted.devices[0].observed_at


def test_corrupt_optional_annotations_do_not_hide_factual_reports(tmp_path):
    store = JsonStore(tmp_path)
    doc = report()
    store._create_scan(doc)
    store._atomic_write(store.data_root / "nicknames.json", "interrupted synthetic write")
    store._atomic_write(store._scan_dir(doc.scan_id) / "annotations.json", "invalid test title")
    page = search_reports(store)
    assert page["total"] == 1
    assert page["items"][0]["storage_status"] == "ok"
    assert len(page["warnings"]) == 2


def test_unreadable_reports_are_separate_from_matches_and_pagination(tmp_path):
    store = JsonStore(tmp_path)
    good, broken = report(), report()
    for doc in (good, broken):
        store._create_scan(doc)
    store._atomic_write(store._scan_dir(broken.scan_id) / "scan.json", "broken")
    page = search_reports(store, q="not-a-match", profile="deep-tcp-v1", limit=1)
    assert page["items"] == [] and page["total"] == 0
    assert page["unreadable_count"] == 1
    assert "files are preserved" in page["warnings"][0]
    page = search_reports(store, limit=1)
    assert page["total"] == 1 and page["items"][0]["scan_id"] == good.scan_id


def test_search_cache_avoids_full_parsing_and_observes_edits(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    doc = report()
    store._create_scan(doc)
    calls = []
    load = store._load_scan

    def counted(scan_id):
        calls.append(scan_id)
        return load(scan_id)

    monkeypatch.setattr(store, "_load_scan", counted)
    assert search_reports(store, q="example")["total"] == 1
    assert search_reports(store, q="not-present")["total"] == 0
    assert len(calls) == 1
    AnnotationStore(store)._update(
        doc.scan_id, title=TitleUpdate(expected_revision=1, title="New title")
    )
    assert search_reports(store, q="new title")["total"] == 1
    NicknameStore(store)._update(
        doc,
        doc.devices[0].device_id,
        NicknameUpdate(expected_revision=1, nickname="Updated nickname"),
    )
    assert search_reports(store, q="updated nickname")["total"] == 1
    doc.devices[0].hostname = "Changed host"
    store._atomic_write(store._scan_dir(doc.scan_id) / "scan.json", doc.model_dump_json())
    assert search_reports(store, q="changed host")["total"] == 1
    assert search_reports(store, q="example")["total"] == 0
    store._atomic_write(store._scan_dir(doc.scan_id) / "scan.json", "unreadable now")
    assert search_reports(store)["unreadable_count"] == 1
    assert search_reports(store)["total"] == 0


def test_library_cache_is_bounded_isolated_and_checks_terminal_overlay(tmp_path):
    first, second = JsonStore(tmp_path / "one"), JsonStore(tmp_path / "two")
    one, two = report(), report()
    for doc in (one, two):
        first._create_scan(doc)
    first.library_cache = LibraryCache(max_entries=1)
    search_reports(first)
    assert len(first.library_cache.entries) == 1
    assert not second.library_cache.entries
    first.library_cache = LibraryCache(max_bytes=1)
    assert search_reports(first)["total"] == 2
    assert not first.library_cache.entries
    first.library_cache = LibraryCache()
    assert search_reports(first)["total"] == 2
    first._atomic_write(first._scan_dir(one.scan_id) / "terminal.json", "invalid overlay")
    # A previously cached good projection must not hide a newly invalid overlay.
    assert search_reports(first)["unreadable_count"] == 1


def test_library_cache_does_not_retain_a_racing_write(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    doc = report()
    store._create_scan(doc)
    load = store._load_scan

    def racing_load(scan_id):
        snapshot = load(scan_id)
        doc.devices[0].hostname = "Updated during read"
        store._atomic_write(store._scan_dir(scan_id) / "scan.json", doc.model_dump_json())
        return snapshot

    monkeypatch.setattr(store, "_load_scan", racing_load)
    store.library_cache.load(store, doc.scan_id)
    assert not store.library_cache.entries
    monkeypatch.setattr(store, "_load_scan", load)
    assert search_reports(store, q="updated during read")["total"] == 1


def test_library_cache_concurrent_readers_share_projection(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    store = JsonStore(tmp_path)
    doc = report()
    store._create_scan(doc)
    calls = []
    load = store._load_scan

    def counted(scan_id):
        calls.append(scan_id)
        return load(scan_id)

    monkeypatch.setattr(store, "_load_scan", counted)
    with ThreadPoolExecutor(max_workers=4) as executor:
        values = list(executor.map(lambda _: search_reports(store)["total"], range(8)))
    assert values == [1] * 8
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("state", "reachability", "expected"),
    [
        ("completed", "observed", "Last device check finished; not proof of safety"),
        ("failed", "advertised", "Last device check did not finish"),
        ("timed_out", "unconfirmed", "Last device check timed out"),
        ("not_scheduled", "advertised", "Advertised its presence"),
        ("not_scheduled", "unconfirmed", "Address saved; response not confirmed"),
    ],
)
def test_picker_retains_uncertainty(tmp_path, state, reachability, expected):
    from app.schemas.scan import TargetLedgerEntry

    store = JsonStore(tmp_path)
    doc = report()
    doc.devices[0].reachability = reachability
    doc.coverage.targets = [TargetLedgerEntry(ip=doc.devices[0].ip, service_status=state)]
    store._create_scan(doc)
    page = search_reports(store, profile="light", scope="192.168.0.0/24", recent_devices=True)
    assert page["items"][0]["check_status"] == state
    assert page["items"][0]["last_check"].startswith(expected)


@pytest.mark.asyncio
async def test_nickname_snapshot_unchanged_and_removed(tmp_path):
    store = JsonStore(tmp_path)
    doc = report()
    store._create_scan(doc)
    names = NicknameStore(store)
    assert await names.snapshot(doc, 1) == {"revision": 1, "changed": False}
    names._update(doc, doc.devices[0].device_id, NicknameUpdate(expected_revision=1, nickname="TV"))
    assert (await names.snapshot(doc, 1))["names"] == {doc.devices[0].device_id: "TV"}
    names._update(doc, doc.devices[0].device_id, NicknameUpdate(expected_revision=2, nickname=""))
    assert (await names.snapshot(doc, 2))["names"] == {}


@pytest.mark.asyncio
async def test_name_only_lookup_has_target_source_time_and_preserves_original():
    from app.schemas.scan import DiscoveryObservation

    doc = report()
    device = doc.devices[0]
    original = device.model_dump()

    async def resolver(ip):
        assert ip == device.ip
        return "example.local"

    async def browser(scope, interface_ip, cancel, **kwargs):
        assert kwargs["target_ips"] == {device.ip}
        assert kwargs["duration_s"] == 3
        return [
            DiscoveryObservation(
                ip=device.ip, advertised_name="Living room", service_type="_http._tcp.local."
            )
        ]

    result = await lookup_names(
        device, "192.168.0.0/24", "192.168.0.2", resolver=resolver, browser=browser
    )
    assert {item["source"] for item in result.names} == {"reverse_dns", "mdns"}
    assert all(item["observed_at"] for item in result.names)
    assert device.model_dump() == original


@pytest.mark.asyncio
async def test_name_lookup_unavailable_does_not_invent_name():
    async def resolver(ip):
        raise OSError("synthetic")

    result = await lookup_names(report().devices[0], "192.168.0.0/24", resolver=resolver)
    assert result.names == []
    assert any("No name was found" in item for item in result.notes)


def test_library_api_security_annotations_and_scope(monkeypatch):
    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.0.0/24")
    monkeypatch.setattr("app.api.library.detect_private_network", lambda: "192.168.0.0/24")
    calls = []

    async def fake_lookup(device, scope, interface):
        calls.append(device.ip)
        return NameRefresh(device_id=device.device_id, checked_at=iso_z(utc_now()))

    monkeypatch.setattr("app.api.library.lookup_names", fake_lookup)
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        doc = report()
        client.portal.call(client.app.state.store.create_scan, doc)
        for url in (
            "/api/reports",
            "/api/recent-devices",
            "/api/running-scans",
            f"/api/live-scans/{doc.scan_id}/nicknames",
            f"/api/live-scans/{doc.scan_id}/annotations",
        ):
            assert client.get(url).status_code == 401
        headers = authenticate_client(client, manager)
        assert client.get("/api/reports?profile=invalid").status_code == 422
        assert client.get("/api/reports?after=2026-10-01&before=2026-09-01").status_code == 422
        url = f"/api/live-scans/{doc.scan_id}/devices/{doc.devices[0].device_id}/refresh-name"
        assert client.post(url, json={"authorised": True}).status_code == 403
        assert client.post(url, headers=headers, json={"authorised": False}).status_code == 422
        assert calls == []
        assert client.post(url, headers=headers, json={"authorised": True}).status_code == 200
        assert calls == [doc.devices[0].ip]
        monkeypatch.setattr("app.api.library.detect_private_network", lambda: "10.20.0.0/24")
        assert client.post(url, headers=headers, json={"authorised": True}).status_code == 409
        assert len(calls) == 1
        title_url = f"/api/live-scans/{doc.scan_id}/title"
        assert (
            client.put(
                title_url, headers=headers, json={"title": "Check", "expected_revision": 2}
            ).status_code
            == 200
        )
        assert (
            client.put(
                title_url, headers=headers, json={"title": "Lost", "expected_revision": 2}
            ).status_code
            == 409
        )
