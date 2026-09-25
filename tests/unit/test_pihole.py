import json

import httpx
import pytest
from app.scanner.pihole import PiholeClient, apply_pihole_names, local_pihole_url
from app.schemas.scan import Device


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "http://8.8.8.8",
        "http://169.254.169.254",
        "http://user:secret@192.168.0.2",
        "http://192.168.0.2/api",
        "http://192.168.0.2/?key=secret",
    ],
)
def test_pihole_connection_rejects_nonlocal_or_embedded_credentials(url):
    with pytest.raises(ValueError):
        local_pihole_url(url)


@pytest.mark.asyncio
async def test_pihole_reads_names_in_scope_and_logs_out_without_network_mutations():
    calls = []

    async def handler(request):
        calls.append((request.method, request.url.path))
        if request.method == "POST":
            assert json.loads(request.content) == {"password": "test-secret"}
            return httpx.Response(200, json={"session": {"valid": True, "sid": "test-session"}})
        assert request.headers["X-FTL-SID"] == "test-session"
        assert "test-secret" not in str(request.url)
        if request.url.path == "/api/network/devices":
            assert request.url.params["max_devices"] == "1024"
            return httpx.Response(
                200,
                json={
                    "devices": [
                        {
                            "hwaddr": "aa:bb:cc:dd:ee:ff",
                            "ips": [
                                {
                                    "ip": "192.168.0.2",
                                    "name": "printer.local",
                                    "lastSeen": 1234567890,
                                },
                                {"ip": "10.0.0.2", "name": "outside", "lastSeen": 1234567890},
                            ],
                        }
                    ]
                },
            )
        if request.url.path == "/api/dhcp/leases":
            return httpx.Response(
                200,
                json={
                    "leases": [
                        {
                            "ip": "192.168.0.3",
                            "name": "tv",
                            "hwaddr": "00:11:22:33:44:55",
                            "expires": 0,
                        },
                        {"ip": "192.168.0.4", "name": "expired", "expires": 1},
                    ]
                },
            )
        return httpx.Response(204)

    records = await PiholeClient(
        "http://192.168.0.1", "test-secret", transport=httpx.MockTransport(handler)
    ).names("192.168.0.0/24")
    assert {item["name"] for item in records} == {"printer.local", "tv"}
    assert calls == [
        ("POST", "/api/auth"),
        ("GET", "/api/network/devices"),
        ("GET", "/api/dhcp/leases"),
        ("DELETE", "/api/auth"),
    ]


def test_historical_ip_name_requires_matching_mac_and_never_changes_reachability():
    device = Device(device_id="device", scan_id="scan", ip="192.168.0.2", mac="aa:bb:cc:dd:ee:ff")
    record = {
        "ip": device.ip,
        "name": "printer",
        "source": "pihole_network",
        "mac": "00:11:22:33:44:55",
        "observed_at": "2026-01-01T00:00:00Z",
    }
    apply_pihole_names([device], [record])
    assert device.hostname is None
    record["mac"] = device.mac
    apply_pihole_names([device], [record])
    assert device.hostname == "printer" and device.hostname_source == "pihole_network"
    assert device.reachability == "unconfirmed"
    assert device.mac == record["mac"]
