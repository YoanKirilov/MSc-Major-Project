import asyncio
import socket
import subprocess
from pathlib import Path

import pytest
from tests.fixtures.offline import OfflineAccessError, install_offline_guard, require_loopback


@pytest.mark.parametrize(
    "host", ["192.168.0.1", "224.0.0.251", "8.8.8.8", "ff02::fb", "services.nvd.nist.gov"]
)
def test_external_dns_tcp_and_udp_are_blocked_before_io(host):
    with pytest.raises(OfflineAccessError):
        socket.getaddrinfo(host, 80)
    for resolver in (socket.gethostbyname, socket.gethostbyname_ex, socket.gethostbyaddr):
        with pytest.raises(OfflineAccessError):
            resolver(host)
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    with socket.socket(family) as sock:
        with pytest.raises(OfflineAccessError):
            sock.connect((host, 80))
        with pytest.raises(OfflineAccessError):
            sock.connect_ex((host, 80))
    with socket.socket(family, socket.SOCK_DGRAM) as sock:
        with pytest.raises(OfflineAccessError):
            sock.sendto(b"must-not-send", (host, 5353))
        with pytest.raises(OfflineAccessError):
            sock.sendto(b"must-not-send", 0, (host, 5353))


@pytest.mark.parametrize("command", ["nmap", "nmap.exe", "powershell.exe", "pwsh", "cmd.exe"])
def test_scanner_and_shell_cannot_be_launched(command):
    with pytest.raises(OfflineAccessError):
        subprocess.Popen([command, "must-not-run"])


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "localhost", b"127.0.0.1"])
def test_literal_loopback_and_localhost_are_allowed(host):
    require_loopback(host)


@pytest.mark.asyncio
async def test_async_connections_cannot_bypass_socket_guard():
    loop = asyncio.get_running_loop()
    with pytest.raises(OfflineAccessError):
        await loop.create_connection(asyncio.Protocol, "192.168.0.1", 80)
    with pytest.raises(OfflineAccessError):
        await loop.create_datagram_endpoint(
            asyncio.DatagramProtocol, remote_addr=("224.0.0.251", 5353)
        )


@pytest.mark.parametrize("allowed", [False, True])
def test_explicit_browser_opt_in_permits_only_its_exact_packaged_driver(monkeypatch, allowed):
    driver = Path("synthetic-driver/node.exe").absolute()
    calls = []
    # Exercise the process allow-list without actually starting Node or a browser.
    monkeypatch.setattr(subprocess.Popen, "__init__", lambda self, args, **kw: calls.append(args))
    monkeypatch.setattr("tests.fixtures.offline.browser_driver_executable", lambda: driver)
    install_offline_guard(monkeypatch, allow_browser=allowed)
    if allowed:
        subprocess.Popen.__init__(object(), [str(driver)])
        assert calls == [[str(driver)]]
    else:
        with pytest.raises(OfflineAccessError):
            subprocess.Popen.__init__(object(), [str(driver)])
        assert not calls
    with pytest.raises(OfflineAccessError):
        subprocess.Popen.__init__(object(), ["other-folder/node.exe"])
