from datetime import datetime, timedelta, timezone

import pytest
from app.schemas.common import iso_z
from app.storage.json_store import JsonStore
from app.storage.library import search_reports
from tests.unit.test_library import report

NOW = datetime(2026, 10, 8, 12, tzinfo=timezone.utc)


@pytest.fixture
def clock(monkeypatch):
    monkeypatch.setattr("app.storage.library.utc_now", lambda: NOW)


def save(store, created, name="Example"):
    doc = report(hostname=name)
    doc.created_at = created
    doc.devices[0].observed_at = created
    store._create_scan(doc)
    return doc


def test_summary_pagination_orders_instants_not_offset_strings(tmp_path):
    store = JsonStore(tmp_path)
    older = save(store, "2026-10-08T01:00:00+03:00")
    newer = save(store, "2026-10-07T23:30:00Z")
    page = store._list_scans(source="live", offset=0, limit=1)
    assert page["items"][0]["scan_id"] == newer.scan_id
    assert (
        store._list_scans(source="live", offset=1, limit=1)["items"][0]["scan_id"] == older.scan_id
    )


@pytest.mark.parametrize(
    "created", ["not-a-date", "2026-10-08T11:00:00", "9999-12-31T23:59:59-23:00"]
)
def test_uncertain_date_remains_searchable_without_rewriting_evidence(tmp_path, created):
    store = JsonStore(tmp_path)
    uncertain = save(store, created, "Uncertain date device")
    known = save(store, iso_z(NOW))
    primary = store._scan_dir(uncertain.scan_id) / "scan.json"
    original = primary.read_bytes()
    summaries = store._list_scans(source="live", offset=0, limit=2)["items"]
    assert [item["scan_id"] for item in summaries] == [known.scan_id, uncertain.scan_id]
    result = search_reports(store, q="uncertain date device")
    assert result["total"] == 1
    assert result["unreadable_count"] == 0
    assert any("date" in warning and "available" in warning for warning in result["warnings"])
    assert primary.read_bytes() == original


@pytest.mark.parametrize(
    "created", ["invalid", "2026-10-08T11:00:00", iso_z(NOW + timedelta(days=1))]
)
def test_device_picker_excludes_uncertain_and_future_reports(tmp_path, clock, created):
    store = JsonStore(tmp_path)
    save(store, created, "Not a recent observation")
    good = save(store, iso_z(NOW - timedelta(hours=1)), "Recent device")
    result = search_reports(store, profile="light", scope="192.168.0.0/24", recent_devices=True)
    assert [item["scan_id"] for item in result["items"]] == [good.scan_id]


def test_picker_uses_latest_instant_and_original_observation(tmp_path, clock):
    store = JsonStore(tmp_path)
    save(store, "2026-10-08T01:00:00+03:00", "Older device name")
    newer = save(store, "2026-10-07T23:30:00Z", "Latest device name")
    result = search_reports(store, profile="light", scope="192.168.0.0/24", recent_devices=True)
    assert result["items"][0]["scan_id"] == newer.scan_id
    assert result["items"][0]["name"] == "Latest device name"
    assert result["items"][0]["observed_at"] == newer.devices[0].observed_at


def test_date_filters_use_utc_day_and_exclude_unknown_dates(tmp_path):
    store = JsonStore(tmp_path)
    wanted = save(store, "2026-10-08T00:30:00+02:00")  # Still October 7 in UTC.
    save(store, "not-a-date")
    day = datetime(2026, 10, 7).date()
    result = search_reports(store, after=day, before=day)
    assert [item["scan_id"] for item in result["items"]] == [wanted.scan_id]
    assert result["unreadable_count"] == 0
