from copy import deepcopy

import pytest
from app.scanner.certificates import certificate_dates
from app.scanner.observations import existing_details
from app.schemas.scan import Device, Service

PERIOD = "Not valid before: 2020-01-01T00:00:00\nNot valid after: 2021-01-01T00:00:00"


def endpoint(output=PERIOD, **changes):
    return Service.model_validate(
        {
            "service_id": "s443",
            "device_id": "device",
            "port": 443,
            "state": "open",
            "observed_at": "2020-06-01T12:00:00Z",
            "script_results": [{"script_id": "ssl-cert", "output": output}],
            **changes,
        }
    )


@pytest.mark.parametrize(
    "when,expected",
    [
        ("2019-12-31T23:59:59Z", "not yet within"),
        ("2020-01-01T00:00:00Z", "within its date window"),
        ("2020-06-01T13:00:00+01:00", "within its date window"),
        ("2021-01-01T00:00:00Z", "within its date window"),
        ("2021-01-01T00:00:01Z", "had expired"),
    ],
)
def test_certificate_uses_recorded_check_not_current_clock(when, expected):
    service = endpoint(observed_at=when)
    text, status = certificate_dates(service)
    assert expected in text
    assert status == "observed"
    assert "Dates alone do not verify" in text
    assert "Do not bypass browser warnings" in text
    assert len(text) <= 600
    if expected == "within its date window":
        assert "not a safety pass" in text


@pytest.mark.parametrize(
    "output",
    [
        "",
        "ERROR: Script execution failed\n" + PERIOD,
        "Script execution failed\n" + PERIOD,
        "Not valid after: 2021-01-01T00:00:00",
        "Not valid before: 2020-01-01T00:00:00",
        PERIOD + "\nNot valid after: 2021-01-01T00:00:00",
        PERIOD + "\nNot valid after: incomplete date",
        PERIOD.replace("2021-01-01", "2018-01-01"),
        PERIOD.replace("2021-01-01", "2021-02-30"),
        PERIOD.replace("2021-01-01", "0000-01-01"),
        PERIOD.replace("2021-01-01T00:00:00", "2021-01-01T00:00:00 injected"),
        PERIOD.replace("2021-01-01T00:00:00", "2021-01-01T00:00:00+01:00"),
        "Subject: " + "x" * 1024 + "\n" + PERIOD,
    ],
)
def test_ambiguous_incomplete_invalid_error_and_unbounded_output_never_pass(output):
    text, status = certificate_dates(endpoint(output))
    assert status == "unavailable"
    assert "could not be checked reliably" in text
    assert "within its date window when checked" not in text


@pytest.mark.parametrize(
    "when", ["", "invalid", "2020-06-01", "2020-06-01T12:00:00", "0001-01-01T00:00:00+14:00"]
)
def test_missing_or_timezone_free_check_time_is_unavailable(when):
    assert certificate_dates(endpoint(observed_at=when))[1] == "unavailable"


@pytest.mark.parametrize("state", ["closed", "filtered", "open_filtered", "unknown"])
def test_certificate_does_not_promote_non_open_evidence(state):
    assert certificate_dates(endpoint(state=state))[1] == "unavailable"


def test_duplicate_scripts_and_truncated_output_are_not_date_verdicts():
    service = endpoint()
    service.script_results.append(service.script_results[0].model_copy())
    assert certificate_dates(service)[1] == "unavailable"
    service.script_results.pop()
    service.script_results[0].truncated = True
    assert certificate_dates(service)[1] == "unavailable"
    service.script_results = []
    assert certificate_dates(service) is None


def test_crlf_z_dates_and_repeated_interpretation_preserve_endpoint_evidence():
    service = endpoint(PERIOD.replace("00:00:00", "00:00:00Z").replace("\n", "\r\n"))
    before = deepcopy(service.model_dump())
    device = Device(device_id="device", scan_id="synthetic", ip="192.168.56.10")
    existing_details(device, [service], [])
    existing_details(device, [service], [])
    assert len(device.details) == 1
    assert device.details[0].observed_at == service.observed_at
    assert "2020-06-01T12:00:00Z" in device.details[0].value
    assert "within its date window" in device.details[0].value
    assert service.model_dump() == before
