import pytest
from app.scanner.commands import MAX_KNOWN_HOSTS
from app.schemas.api import ScanCreateRequest
from app.security.scope import validate_target
from pydantic import ValidationError


def request(hosts):
    return {"mode": "known_hosts", "hosts": hosts, "authorised": True}


def test_same_explicit_limit_in_schema_and_standalone_validator():
    hosts = [f"192.168.56.{n}" for n in range(1, 255)]
    settings = {"allowed_network": "192.168.0.0/16"}
    assert len(ScanCreateRequest(**request(hosts)).hosts) == MAX_KNOWN_HOSTS
    assert len(validate_target(request(hosts), settings).hosts) == MAX_KNOWN_HOSTS
    hosts.append("192.168.57.1")
    with pytest.raises(ValidationError):
        ScanCreateRequest(**request(hosts))
    with pytest.raises(ValueError, match="at most"):
        validate_target(request(hosts), settings)


@pytest.mark.parametrize(
    "host", ["", "1" * 1000, "192.168.056.1", "::1", "8.8.8.8", "192.168.57.1", 3232249857, None]
)
def test_standalone_validator_rejects_bad_or_out_of_scope_hosts(host):
    with pytest.raises(ValueError):
        validate_target(request([host]), {"allowed_network": "192.168.56.0/24"})


@pytest.mark.parametrize(
    "field,value",
    [
        ("mode", "x" * 17),
        ("cidr", "x" * 19),
        ("profile", "x" * 33),
        ("hosts", ["x" * 16]),
        ("hosts", [3232249857]),
    ],
)
def test_schema_text_limits(field, value):
    body = {**request(["192.168.56.1"]), field: value}
    with pytest.raises(ValidationError):
        ScanCreateRequest(**body)
