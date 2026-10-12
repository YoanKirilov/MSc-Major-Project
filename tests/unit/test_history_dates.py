"""Untrusted saved timestamps must not hide valid history or invent chronology."""

import pytest
from app.profiling.history import compare_history, earlier_observations, restore_previous_name
from app.storage.nicknames import matches
from tests.unit.test_earlier_observations import add_device, report
from tests.unit.test_name_reliability import pair
from tests.unit.test_nicknames import document


def test_invalid_previous_timestamp_does_not_hide_other_compatible_reports():
    current, valid, invalid = report(8), report(7), report(6)
    add_device(valid, 10)
    invalid.created_at = "not-a-date"
    result = earlier_observations(current, [invalid, valid])
    assert result.status == "available"
    assert result.source_scan_id == valid.scan_id and len(result.items) == 1


def test_earlier_view_selects_the_latest_instant_not_the_latest_date_string():
    current, recent, older = report(8), report(7), report(6)
    recent.created_at = "2026-10-07T20:00:00Z"
    older.created_at = "2026-10-08T01:00:00+10:00"  # 15:00 UTC, not the newer report.
    add_device(recent, 10)
    add_device(older, 11)
    result = earlier_observations(current, [recent, older])
    assert result.source_scan_id == recent.scan_id
    assert [item.last_ip for item in result.items] == ["192.168.56.10"]


def test_service_history_accepts_a_previous_instant_with_a_later_local_date():
    current, old = pair()
    old.created_at = "2026-09-26T01:00:00+04:00"  # 21:00 UTC, before current 22:00 UTC.
    old.devices[0].hostname_observed_at = old.created_at
    compare_history(current, [old])
    assert current.devices[0].hostname == "Room TV"
    assert any(item.label == "Previously seen" for item in current.devices[0].details)


def test_service_history_does_not_accept_a_future_instant_with_an_earlier_date_string():
    current, future = pair()
    future.created_at = "2026-09-25T20:00:00-04:00"  # 00:00 UTC the next day.
    compare_history(current, [future])
    assert not any(item.label == "Previously seen" for item in current.devices[0].details)


@pytest.mark.parametrize("date", ["not-a-date", "2026-09-25T21:00:00", "9999-12-31T23:59:59-23:00"])
def test_uncertain_name_times_are_skipped_without_hiding_another_valid_name(date):
    current, valid = pair()
    invalid = valid.model_copy(deep=True)
    invalid.devices[0].hostname_observed_at = date
    restore_previous_name(
        current.devices[0],
        [(invalid, invalid.devices[0]), (valid, valid.devices[0])],
        current.created_at,
    )
    assert current.devices[0].hostname == "Room TV"
    assert current.devices[0].hostname_observed_at == valid.created_at


@pytest.mark.parametrize("date", ["not-a-date", "2026-09-26T12:00:00", "9999-12-31T23:59:59-23:00"])
def test_invalid_or_timezone_free_anchor_never_reuses_a_nickname(date):
    source, current = document(), document("2026-09-27T12:00:00Z")
    source.created_at = date
    assert matches(current, current.devices[0], source, source.devices[0]) is False


def test_timezone_free_current_report_is_not_compared_but_exact_nickname_still_matches():
    current, old = pair()
    current.created_at = "2026-09-25T22:00:00"
    compare_history(current, [old])
    assert current.devices[0].hostname is None
    assert not any(item.label == "Previously seen" for item in current.devices[0].details)
    assert matches(current, current.devices[0], current, current.devices[0]) is True
