import asyncio

import pytest
from app.scanner import mdns


def test_mdns_browse_filters_out_of_scope_advertisements(monkeypatch):
    class FakeInfo:
        server = "printer.local."
        port = 631
        properties = {}

        def get_name(self):
            return "Living room printer"

        def parsed_addresses(self, version):
            return ["192.168.0.5", "192.168.91.5"]

    class FakeZeroconf:
        def __init__(self, *, interfaces, ip_version):
            assert interfaces == ["192.168.0.216"]

        def get_service_info(self, type_, name, timeout):
            return FakeInfo()

        def close(self):
            pass

    class FakeBrowser:
        def __init__(self, zc, types, listener):
            listener.add_service(zc, "_ipp._tcp.local.", "Living room printer")

        def cancel(self):
            pass

    monkeypatch.setattr(mdns, "Zeroconf", FakeZeroconf)
    monkeypatch.setattr(mdns, "ServiceBrowser", FakeBrowser)
    monkeypatch.setattr(mdns, "ServiceListener", object)
    observations = mdns._browse("192.168.0.0/24", "192.168.0.216", 0, asyncio.Event())
    assert len(observations) == 1
    assert observations[0].ip == "192.168.0.5"
    assert observations[0].evidence_type == "advertisement"


def test_mdns_rejects_interface_outside_authorised_scope():
    with pytest.raises(ValueError, match="outside"):
        mdns._browse("192.168.0.0/24", "192.168.91.1", 0, asyncio.Event())


def test_mdns_limits_new_hosts_added_to_a_scan(monkeypatch):
    class FakeInfo:
        server = None
        port = None
        properties = {}

        def __init__(self, address):
            self.address = address

        def get_name(self):
            return "Advertised device"

        def parsed_addresses(self, version):
            return [self.address]

    class FakeZeroconf:
        def __init__(self, *, interfaces, ip_version):
            pass

        def get_service_info(self, type_, name, timeout):
            return FakeInfo(name)

        def close(self):
            pass

    class FakeBrowser:
        def __init__(self, zc, types, listener):
            for last_octet in range(1, 13):
                listener.add_service(zc, "_ipp._tcp.local.", f"192.168.0.{last_octet}")

        def cancel(self):
            pass

    monkeypatch.setattr(mdns, "Zeroconf", FakeZeroconf)
    monkeypatch.setattr(mdns, "ServiceBrowser", FakeBrowser)
    monkeypatch.setattr(mdns, "ServiceListener", object)

    observations = mdns._browse("192.168.0.0/24", "192.168.0.216", 0, asyncio.Event())
    assert len({item.ip for item in observations}) == mdns.MAX_UNIQUE_HOSTS
