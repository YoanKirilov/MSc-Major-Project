import pytest
from app.security.scope import validate_target

SETTINGS = {"allowed_network": "192.168.56.0/24", "profile_id": "tcp12-udp3-v5"}


def test_discover_restricts_to_private_subnet_and_eligible_hosts():
    target = validate_target(
        {"mode": "discover", "cidr": "192.168.56.0/30", "authorised": True}, SETTINGS
    )
    assert target.candidates == ("192.168.56.1", "192.168.56.2")


def test_known_hosts_are_sorted_and_deduplicated():
    target = validate_target(
        {"mode": "known_hosts", "hosts": ["192.168.56.20", "192.168.56.2"], "authorised": True},
        SETTINGS,
    )
    assert target.hosts == ("192.168.56.2", "192.168.56.20")
    with pytest.raises(ValueError, match="duplicate"):
        validate_target(
            {"mode": "known_hosts", "hosts": ["192.168.56.2", "192.168.56.2"], "authorised": True},
            SETTINGS,
        )


@pytest.mark.parametrize(
    "cidr", ["8.8.8.0/24", "192.168.57.0/24", "192.168.56.0/23", "192.168.56.1/24"]
)
def test_out_of_scope_or_noncanonical_targets_rejected(cidr):
    with pytest.raises(ValueError):
        validate_target({"mode": "discover", "cidr": cidr, "authorised": True}, SETTINGS)
