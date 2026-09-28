import asyncio
from types import SimpleNamespace

import pytest
from app.scanner import mdns


def info(ip="192.168.0.5", name="Living room printer"):
    return SimpleNamespace(
        server="printer.local.",
        port=631,
        properties={b"model": b"Example"},
        get_name=lambda: name,
        parsed_addresses=lambda version: [ip, "192.168.91.5"],
    )


@pytest.fixture
def browser_fixture(monkeypatch):
    state = SimpleNamespace(
        events=["printer"],
        replies={"printer": [info()]},
        calls=[],
        active=0,
        peak=0,
        closed=False,
        browser_closed=False,
        stall=False,
    )

    class FakeZeroconf:
        def __init__(self, **kwargs):
            assert kwargs["interfaces"] == ["192.168.0.216"]
            self.zeroconf = self

        async def async_get_service_info(self, type_, name, timeout):
            state.calls.append((name, timeout))
            state.active += 1
            state.peak = max(state.peak, state.active)
            try:
                if state.stall:
                    await asyncio.Event().wait()
                await asyncio.sleep(0)
                replies = state.replies[name]
                value = replies.pop(0) if len(replies) > 1 else replies[0]
                if isinstance(value, Exception):
                    raise value
                return value
            finally:
                state.active -= 1

        async def async_close(self):
            state.closed = True

    class FakeBrowser:
        def __init__(self, zc, types, listener):
            for name in state.events:
                listener.add_service(zc, "_ipp._tcp.local.", name)

        async def async_cancel(self):
            state.browser_closed = True

    monkeypatch.setattr(mdns, "AsyncZeroconf", FakeZeroconf)
    monkeypatch.setattr(mdns, "AsyncServiceBrowser", FakeBrowser)
    monkeypatch.setattr(mdns, "ServiceListener", object)
    return state


async def browse(**kwargs):
    return await mdns.browse_mdns(
        "192.168.0.0/24", "192.168.0.216", asyncio.Event(), duration_s=0.05, **kwargs
    )


@pytest.mark.asyncio
async def test_mdns_browse_filters_out_of_scope_advertisements(browser_fixture):
    observations = await browse()
    assert len(observations) == 1
    assert observations[0].ip == "192.168.0.5"
    assert observations[0].evidence_type == "advertisement"
    assert browser_fixture.closed and browser_fixture.browser_closed


@pytest.mark.asyncio
async def test_mdns_rejects_interface_outside_authorised_scope():
    with pytest.raises(ValueError, match="outside"):
        await mdns.browse_mdns("192.168.0.0/24", "192.168.91.1", asyncio.Event(), 0)


@pytest.mark.asyncio
async def test_mdns_limits_new_hosts_added_to_a_scan(browser_fixture):
    state = browser_fixture
    state.events = [str(n) for n in range(1, 13)]
    state.replies = {name: [info(f"192.168.0.{name}")] for name in state.events}
    observations = await browse()
    assert len({item.ip for item in observations}) == mdns.MAX_UNIQUE_HOSTS


@pytest.mark.asyncio
async def test_mdns_filters_known_hosts_before_limit_and_keeps_metadata(browser_fixture):
    state = browser_fixture
    state.events = [str(n) for n in range(1, 13)]
    state.replies = {name: [info(f"192.168.0.{name}")] for name in state.events}
    observations = await browse(target_ips={"192.168.0.12"})
    assert len(observations) == 1 and observations[0].ip == "192.168.0.12"
    assert observations[0].port == 631 and observations[0].hostname == "printer.local."
    assert observations[0].properties == {"model": "Example"}


@pytest.mark.asyncio
async def test_mdns_retries_unresolved_services_without_new_callback(browser_fixture):
    state = browser_fixture
    state.replies["printer"] = [None, info()]
    observations = await browse()
    assert len(observations) == 1 and len(state.calls) == 2
    assert all(timeout == 750 for _, timeout in state.calls)


@pytest.mark.asyncio
async def test_mdns_callbacks_dont_serially_block_other_devices(browser_fixture):
    state = browser_fixture
    state.events = ["slow", "printer"]
    state.replies["slow"] = [ValueError("malformed service"), None]
    observations = await browse()
    assert observations[0].advertised_name == "Living room printer"
    assert state.peak == 2


@pytest.mark.asyncio
async def test_mdns_cancellation_stops_all_bounded_resolvers(browser_fixture):
    state = browser_fixture
    state.events = [str(n) for n in range(100)]
    state.stall = True
    observations = await browse()
    assert observations == []
    assert state.peak == mdns.LOOKUP_WORKERS and state.active == 0
    assert state.closed and state.browser_closed


@pytest.mark.asyncio
async def test_mdns_cancelled_before_start_does_not_open_browser(browser_fixture):
    cancel = asyncio.Event()
    cancel.set()
    assert await mdns.browse_mdns("192.168.0.0/24", "192.168.0.216", cancel) == []
    assert not browser_fixture.calls and not browser_fixture.closed


@pytest.mark.asyncio
async def test_discovery_subnet_filters_before_mdns_cap(tmp_path, browser_fixture):
    from uuid import uuid4

    from app.jobs.supervisor import ScanSupervisor
    from app.scanner.runner import ProcessResult
    from app.schemas.scan import ScanDocument
    from app.storage.json_store import JsonStore

    state = browser_fixture
    state.events = [str(n) for n in range(1, 15)]
    state.replies = {name: [info(f"192.168.0.{name}")] for name in state.events}
    store = JsonStore(tmp_path)
    scan = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "discover", "cidr": "192.168.0.12/30", "hosts": []},
        policy={
            "allowed_network": "192.168.0.0/24",
            "mdns_enabled": True,
            "mdns_interface_ip": "192.168.0.216",
        },
        coverage={
            "candidate_count": 2,
            "targets": [{"ip": "192.168.0.13"}, {"ip": "192.168.0.14"}],
        },
    )
    checked = []

    async def runner(args, *rest):
        host = ""
        if "-sn" not in args:
            checked.append(args[-1])
            host = f'<host><address addrtype="ipv4" addr="{args[-1]}"/></host>'
        xml = f"<nmaprun>{host}<runstats><finished/></runstats></nmaprun>".encode()
        return ProcessResult(xml, b"", 0, 0.01)

    async def browser(scope, interface, cancel, **kwargs):
        return await mdns.browse_mdns(scope, interface, cancel, duration_s=0.05, **kwargs)

    await store.create_scan(scan)
    supervisor = ScanSupervisor(store, process_runner=runner, mdns_browser=browser)
    await supervisor.start(scan.scan_id)
    async with asyncio.timeout(5):
        while supervisor.is_active(scan.scan_id):
            await asyncio.sleep(0.01)
    saved = await store.load_scan(scan.scan_id)
    assert saved.state == "completed"
    assert set(checked) == {"192.168.0.13", "192.168.0.14"}
    assert {item.ip for item in saved.observations} == set(checked)
    assert saved.coverage.discovered_count == 2
