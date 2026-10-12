from datetime import datetime, timezone

import pytest
from app.schemas.common import observation_time


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        [],
        "invalid",
        "2026-10-08",
        "2026-10-08T12:00:00",
        "9999-12-31T23:59:59-23:00",
        "0001-01-01T00:00:00+23:00",
    ],
)
def test_uncertain_or_out_of_range_instants_are_unavailable(value):
    assert observation_time(value) is None


@pytest.mark.parametrize(
    "value", ["2026-10-08T12:00:00Z", "2026-10-08T13:00:00+01:00", "2026-10-08T08:00:00-04:00"]
)
def test_offsets_are_compared_as_the_same_utc_instant(value):
    assert observation_time(value) == datetime(2026, 10, 8, 12, tzinfo=timezone.utc)
