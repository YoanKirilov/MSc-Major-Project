import json
from types import SimpleNamespace

import pytest
from app.scanner.network import SnapshotUnavailable, _connection_rows, _query_windows_connections


def row(**changes):
    return {
        "Index": 11,
        "Profile": "Home",
        "Addresses": [{"IPAddress": "192.168.1.60", "PrefixLength": 24}],
        "Gateways": ["192.168.1.254"],
        **changes,
    }


def test_connection_order_is_not_a_network_change():
    one = row(
        Addresses=[
            {"IPAddress": "192.168.1.60", "PrefixLength": 24},
            {"IPAddress": "192.168.1.61", "PrefixLength": 24},
        ],
        Gateways=["192.168.1.254", "192.168.1.1"],
    )
    two = row(Index=19, Profile=None, Gateways=[])
    reordered = {**one, "Addresses": one["Addresses"][::-1], "Gateways": one["Gateways"][::-1]}
    assert _connection_rows([one, two]) == _connection_rows([two, reordered])
    assert _connection_rows(row()) == [row()]
    assert _connection_rows([]) == []  # No match remains unavailable to the guard.


@pytest.mark.parametrize(
    "value",
    [
        None,
        [1],
        [row(), row()],
        [row(Index=True)],
        [row(Index=0)],
        [row(Profile=1)],
        [row(Addresses=None)],
        [row(Gateways=[None])],
        [row(Gateways=["::1"])],
        [row(Addresses=[{"IPAddress": "192.168.1.60"}])],
        [row(Addresses=[{"IPAddress": "::1", "PrefixLength": 24}])],
        [row(Addresses=[{"IPAddress": "192.168.1.60", "PrefixLength": True}])],
        [row(Addresses=[{"IPAddress": "192.168.1.60", "PrefixLength": 33}])],
        [row(Unexpected="partial output")],
        [row(Index=i + 1) for i in range(257)],
    ],
)
def test_connection_output_fails_closed(value):
    with pytest.raises(SnapshotUnavailable, match="adapter_output_invalid"):
        _connection_rows(value)


def test_direct_query_is_bounded_read_only_and_preserves_facts(monkeypatch):
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps([row()]))

    monkeypatch.setattr("app.scanner.network.subprocess.run", run)
    assert _query_windows_connections() == [row()]
    args, kwargs = calls[0]
    assert args[:4] == ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command"]
    assert kwargs["timeout"] == 8
    assert "$ErrorActionPreference='Stop'" in args[4]
    for command in (
        "Get-NetIPAddress",
        "Get-NetIPInterface",
        "Get-NetRoute",
        "Get-NetConnectionProfile",
    ):
        assert command in args[4]
    assert "Get-NetIPConfiguration" not in args[4]
    assert "DestinationPrefix -eq '0.0.0.0/0'" in args[4]
    assert "-ConnectionState Connected" in args[4]
    assert "throw 'Ambiguous connection profile'" in args[4]
