import asyncio
from uuid import uuid4

import httpx
import pytest
from app.jobs.supervisor import ScanSupervisor
from app.profiling.classifier import classify_device
from app.profiling.history import compare_history
from app.risk.engine import evaluate_device
from app.risk.guidance import guidance_status, refresh_guidance
from app.scanner import mdns
from app.scanner.details import (
    netbios_name,
    network_details,
    same_device_url,
)
from app.scanner.observations import detail, existing_details
from app.scanner.runner import ProcessResult
from app.schemas.scan import Device, DeviceDetail, DiscoveryObservation, ScanDocument, Service
from app.storage.json_store import JsonStore


def device():
    return Device(device_id="dev", scan_id=str(uuid4()), ip="192.168.0.20")


def service(port=80, name="http", **kwargs):
    return Service(
        service_id=f"s{port}", device_id="dev", port=port, name=name, state="open", **kwargs
    )


def document(profile="light", created="2026-09-25T22:00:00Z"):
    d = device()
    return ScanDocument(
        scan_id=d.scan_id,
        target={"mode": "known_hosts", "hosts": [d.ip]},
        created_at=created,
        devices=[d],
        phase="finished",
        state="completed",
        policy={
            "allowed_network": "192.168.0.0/24",
            "profile_id": profile,
            "extra_details_enabled": True,
            "tcp_ports": [80, 443],
            "udp_ports": [],
        },
        coverage={"targets": [{"ip": d.ip, "service_status": "completed"}]},
    )


def test_mdns_allowlist_is_small_and_excludes_secrets():
    properties = mdns.safe_properties(
        {
            b"md": b"Example TV",
            b"model": b"x" * 2000,
            b"password": b"secret",
            b"serial": b"private-id",
        }
    )
    assert properties["md"] == "Example TV"
    assert len(properties["model"]) == 120
    assert set(properties) == {"md", "model"}


def test_advertised_type_does_not_promote_reachability_or_open_ports():
    d = device()
    observation = DiscoveryObservation(
        ip=d.ip,
        advertised_name="Room",
        service_type="_googlecast._tcp.local.",
        port=8009,
        properties={"md": "Example TV"},
    )
    existing_details(d, [], [observation])
    result = classify_device(d, [])
    assert result["category"] == "media" and result["confidence"] == "low"
    assert d.reachability == "unconfirmed"
    assert all(item.status == "advertised" for item in d.details)
    d.hostname_conflict = True
    assert classify_device(d, [])["category"] == "unknown"


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/",
        "http://192.168.0.21/",
        "http://127.0.0.1/",
        "http://169.254.169.254/",
        "http://user:secret@192.168.0.20/",  # pragma: allowlist secret - rejected synthetic URL
        "file:///etc/passwd",
        "http://192.168.0.20:0/",
    ],
)
def test_extra_requests_reject_external_or_cross_device_urls(url):
    with pytest.raises(ValueError):
        same_device_url(url, "192.168.0.20", "192.168.0.0/24")


@pytest.mark.asyncio
async def test_http_follows_only_one_same_device_https_redirect():
    calls = []

    async def handler(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://192.168.0.20/"})

    d = device()
    await network_details(d, [service()], "192.168.0.0/24", transport=httpx.MockTransport(handler))
    assert len(calls) == 2 and all("192.168.0.20" in url for url in calls)
    assert "Redirected to HTTPS" in d.details[0].value
    # This mocked test verifies control flow, not a real TLS handshake.


@pytest.mark.asyncio
async def test_http_cross_device_redirect_is_not_followed():
    calls = []

    async def handler(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://192.168.0.21/private"})

    d = device()
    await network_details(d, [service()], "192.168.0.0/24", transport=httpx.MockTransport(handler))
    assert len(calls) == 1 and d.details[0].status == "unavailable"


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["https", "http", "unavailable", "not_checked"])
async def test_http_guidance_is_consistent_with_optional_redirect_checks(outcome):
    doc = document()
    d = doc.devices[0]
    s = service()
    s.service_id = str(uuid4())
    s.detection_method = "probed"
    s.nmap_confidence = 10
    doc.services = [s]
    # Findings are created before optional details in the scan lifecycle.
    doc.findings = evaluate_device(d, [s])

    def handler(request):
        if outcome == "unavailable":
            raise httpx.ConnectError("synthetic failure", request=request)
        if outcome == "https" and request.url.scheme == "http":
            return httpx.Response(302, headers={"location": f"https://{d.ip}/"})
        return httpx.Response(200)

    if outcome != "not_checked":
        await network_details(d, [s], "192.168.0.0/24", transport=httpx.MockTransport(handler))
        if outcome == "https":
            assert "Redirected to HTTPS" in d.details[0].value
        elif outcome == "http":
            assert "no HTTPS redirect" in d.details[0].value
        else:
            assert d.details[0].status == "unavailable"
    finding = doc.findings[0]
    assert "Device details" in finding.fixed_explanation.why_it_matters
    assert "did not check" not in finding.fixed_explanation.why_it_matters
    assert "did not test HTTPS" not in " ".join(finding.limitations)
    assert "root page" in " ".join(finding.limitations)
    assert finding.severity == "low" and finding.confidence == "medium"

    # Saved reports can receive the wording correction through explicit refresh.
    finding.rule_version = "1.1.0"
    finding.limitations = ["The scan did not test HTTPS redirection or page purpose."]
    before = doc.model_dump_json()
    assert guidance_status(doc)["outdated_findings"] == 1
    updated = refresh_guidance(doc)
    assert doc.model_dump_json() == before
    assert updated.devices == doc.devices and updated.services == doc.services
    assert updated.findings[0].finding_id == finding.finding_id
    assert updated.findings[0].evidence == finding.evidence
    assert updated.findings[0].rule_version == "1.1.1"
    assert "did not test HTTPS" not in " ".join(updated.findings[0].limitations)
    assert updated.guidance_history[0].findings[0].limitations == finding.limitations


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [b"x" * 65537, b"<bad", b'<!DOCTYPE x [<!ENTITY a "boom">]><x>&a;</x>'],
    ids=["oversized", "malformed", "entity"],
)
async def test_upnp_rejects_oversized_malformed_or_entity_xml(body):
    d = device()
    s = service(
        1900,
        "upnp",
        protocol="udp",
        script_results=[
            {"script_id": "upnp-info", "output": "Location: http://192.168.0.20/description.xml"}
        ],
    )
    await network_details(
        d,
        [s],
        "192.168.0.0/24",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=body)),
    )
    assert d.hostname is None and d.details[0].status == "unavailable"


@pytest.mark.asyncio
async def test_upnp_retains_root_identity_only_not_serial_or_embedded_device():
    body = b"""<root xmlns="urn:test"><device><friendlyName>Room display</friendlyName>
    <manufacturer>Example</manufacturer><modelName>Model A</modelName>
    <deviceType>urn:schemas-upnp-org:device:MediaRenderer:1</deviceType>
    <serialNumber>PRIVATE</serialNumber><deviceList><device>
    <friendlyName>Other device</friendlyName>
    </device></deviceList></device></root>"""
    d = device()
    s = service(
        1900,
        "upnp",
        protocol="udp",
        script_results=[
            {"script_id": "upnp-info", "output": "Location: http://192.168.0.20/desc.xml"}
        ],
    )
    await network_details(
        d,
        [s],
        "192.168.0.0/24",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=body)),
    )
    assert d.hostname == "Room display" and d.hostname_source == "upnp"
    assert "PRIVATE" not in d.model_dump_json() and "Other device" not in d.model_dump_json()
    assert classify_device(d, [s])["category"] == "media"


@pytest.mark.asyncio
@pytest.mark.parametrize("empty", ["", " ", "(none)", "*"])
async def test_empty_upnp_fields_do_not_abort_other_details(empty):
    d = device()
    s = service(
        1900,
        "upnp",
        protocol="udp",
        script_results=[
            {"script_id": "upnp-info", "output": "Location: http://192.168.0.20/desc.xml"}
        ],
    )
    body = (
        f"<root><device><friendlyName>{empty}</friendlyName>"
        "<manufacturer/><modelName>Example model</modelName></device></root>"
    ).encode()
    await network_details(
        d,
        [s],
        "192.168.0.0/24",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=body)),
    )
    assert d.hostname is None
    assert [(item.label, item.value) for item in d.details] == [("modelName", "Example model")]


def test_history_missing_port_selections_are_not_comparable():
    old, current = document(created="2026-09-24T22:00:00Z"), document()
    old.devices[0].mac = current.devices[0].mac = "aa:bb:cc:dd:ee:ff"
    for doc in (old, current):
        doc.policy.pop("tcp_ports", None)
        doc.policy.pop("udp_ports", None)
    compare_history(current, [old])
    assert current.devices[0].details[-1].status == "not_checked"


@pytest.mark.asyncio
async def test_optional_collection_error_is_not_reported_as_timeout(tmp_path, monkeypatch):
    doc = document()
    store = JsonStore(tmp_path)
    await store.create_scan(doc)

    async def broken(*args, **kwargs):
        raise ValueError("synthetic collector error")

    async def working_name(device, *args, **kwargs):
        detail(device, "netbios", "Computer name", "EXAMPLE", "NetBIOS")

    monkeypatch.setattr("app.scanner.details.network_details", broken)
    monkeypatch.setattr("app.scanner.details.netbios_name", working_name)
    await ScanSupervisor(store)._enrich_details(doc.scan_id, asyncio.Event())
    saved = await store.load_scan(doc.scan_id)
    assert any(item.status == "unavailable" for item in saved.devices[0].details)
    assert "ran out of time" not in saved.devices[0].model_dump_json()
    assert any(item.value == "EXAMPLE" for item in saved.devices[0].details)
    assert saved.state == "completed"


def test_certificate_date_is_not_a_security_verdict():
    d = device()
    s = service(
        443,
        "https",
        script_results=[
            {"script_id": "ssl-cert", "output": "Not valid after: 2001-01-01T00:00:00"}
        ],
    )
    existing_details(d, [s], [])
    assert "Expired" in d.details[0].value and "does not verify" in d.details[0].value


@pytest.mark.asyncio
async def test_netbios_only_keeps_device_name_not_username():
    async def runner(args, timeout, cancel):
        assert args[-1] == "192.168.0.20" and timeout == 5
        xml = b"""<nmaprun><host><address addr="192.168.0.20"/><hostscript>
        <script id="nbstat" output="NetBIOS name: LAPTOP, NetBIOS user: PRIVATE, NetBIOS MAC: AA"/>
        </hostscript></host></nmaprun>"""
        return ProcessResult(xml, b"", 0, 0.01)

    d = device()
    await netbios_name(d, [service(445, "microsoft-ds")], "nmap", runner, asyncio.Event())
    assert d.hostname == "LAPTOP" and d.hostname_source == "netbios"
    assert "PRIVATE" not in d.model_dump_json()


def test_history_requires_matching_mac_scope_profile_and_completed_checks():
    old = document(created="2026-09-24T22:00:00Z")
    current = document()
    old.devices[0].mac = current.devices[0].mac = "aa:bb:cc:dd:ee:ff"
    old.services = [service(80)]
    current.services = [service(443, "https")]
    compare_history(current, [old])
    assert "Newly observed open: TCP 443" in current.devices[0].details[-1].value
    current.devices[0].details = []
    current.policy["profile_id"] = "deep"
    compare_history(current, [old])
    assert current.devices[0].details[-1].status == "not_checked"
    current.devices[0].details = []
    current.devices[0].mac = None
    compare_history(current, [old])
    assert "No usable network-adapter address" in current.devices[0].details[-1].value
    current.devices[0].details = []
    old.policy["allowed_network"] = "192.168.1.0/24"
    compare_history(current, [old])
    assert "No earlier finished report" in current.devices[0].details[-1].value


@pytest.mark.asyncio
@pytest.mark.parametrize("profile", ["light", "deep-tcp-v1"])
async def test_both_profiles_enrich_only_requested_hosts(tmp_path, monkeypatch, profile):
    doc = document(profile)
    doc.policy.update(mdns_enabled=True, mdns_interface_ip="192.168.0.2")
    store = JsonStore(tmp_path)
    await store.create_scan(doc)

    async def browser(scope, interface, cancel, *, target_ips, known_ips):
        assert target_ips == {"192.168.0.20"}
        return [
            DiscoveryObservation(
                ip=ip, advertised_name="Room", service_type="_googlecast._tcp.local."
            )
            for ip in ("192.168.0.20", "192.168.0.21")
        ]

    supervisor = ScanSupervisor(store, mdns_browser=browser)
    await supervisor._known_host_announcements(doc.scan_id, asyncio.Event())
    await supervisor._enrich_names(doc.scan_id, asyncio.Event())
    await supervisor._enrich_details(doc.scan_id, asyncio.Event())
    saved = await store.load_scan(doc.scan_id)
    assert len(saved.devices) == 1 and len(saved.observations) == 1
    assert saved.devices[0].profile.category == "media"


@pytest.mark.asyncio
async def test_optional_timeout_preserves_scan_evidence(tmp_path, monkeypatch):
    doc = document()
    store = JsonStore(tmp_path)
    await store.create_scan(doc)

    async def stalled(*args, **kwargs):
        await asyncio.sleep(60)

    monkeypatch.setattr("app.scanner.details.network_details", stalled)
    supervisor = ScanSupervisor(store)
    supervisor.details_timeout_s = 0.02
    await supervisor._enrich_details(doc.scan_id, asyncio.Event())
    saved = await store.load_scan(doc.scan_id)
    assert saved.state == "completed" and saved.coverage.targets[0].service_status == "completed"
    assert any(d.status == "not_checked" for d in saved.devices[0].details)
    assert saved.warnings[0]["code"] == "EXTRA_DETAILS_INCOMPLETE"


def test_legacy_device_loads_without_new_details():
    d = device()
    data = d.model_dump()
    data.pop("details")
    assert Device.model_validate(data).details == []
    with pytest.raises(ValueError):
        DeviceDetail(kind="web", label="test", value="x" * 601, source="test")


def test_details_deduplicate_and_disclose_limits():
    d = device()
    for _ in range(60):
        detail(d, "mdns", "Model", "Example", "mDNS", "advertised")
    assert len(d.details) == 1
    for number in range(60):
        detail(d, "web", "Title", str(number), "HTTP")
    assert len(d.details) == 48
    assert d.details[-1].label == "Extra information limit"


def test_classification_does_not_double_count_name_from_same_source():
    d = device()
    d.hostname = "bravia"
    d.hostname_source = "upnp"
    detail(d, "upnp", "modelName", "bravia", "UPnP", "advertised")
    assert classify_device(d, [])["confidence"] == "low"


def test_closed_service_does_not_support_device_classification():
    d = device()
    d.hostname = "camera"
    s = service(554, "rtsp")
    s.state = "closed"
    assert classify_device(d, [s])["category"] == "unknown"


@pytest.mark.asyncio
async def test_tls_failure_keeps_http_evidence_without_claiming_verified_upgrade():
    async def handler(request):
        if request.url.scheme == "https":
            raise httpx.ConnectError("certificate verification failed")
        return httpx.Response(301, headers={"location": "https://192.168.0.20/"})

    d = device()
    await network_details(d, [service()], "192.168.0.0/24", transport=httpx.MockTransport(handler))
    assert d.details[0].status == "unavailable"
    assert "Could not verify" in d.details[0].value


@pytest.mark.asyncio
async def test_external_upnp_url_is_never_requested():
    def handler(request):
        pytest.fail("Untrusted UPnP URL was requested")

    d = device()
    s = service(
        1900,
        "upnp",
        protocol="udp",
        script_results=[
            {"script_id": "upnp-info", "output": "Location: http://example.com/device.xml"}
        ],
    )
    await network_details(d, [s], "192.168.0.0/24", transport=httpx.MockTransport(handler))
    assert d.details[0].status == "unavailable"


@pytest.mark.asyncio
async def test_extra_checks_limit_concurrency_and_cancel_cleanly(tmp_path, monkeypatch):
    doc = document()
    doc.devices = [
        Device(device_id=f"d{i}", scan_id=doc.scan_id, ip=f"192.168.0.{i}") for i in range(20, 25)
    ]
    store = JsonStore(tmp_path)
    await store.create_scan(doc)
    cancel = asyncio.Event()
    entered = asyncio.Event()
    active = peak = 0

    async def stalled(*args):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        if active == 2:
            entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            active -= 1

    monkeypatch.setattr("app.scanner.details.network_details", stalled)
    supervisor = ScanSupervisor(store)
    task = asyncio.create_task(supervisor._enrich_details(doc.scan_id, cancel))
    try:
        await asyncio.wait_for(entered.wait(), timeout=5)
        cancel.set()
        await asyncio.wait_for(task, timeout=5)
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    assert peak == 2 and active == 0
    saved = await store.load_scan(doc.scan_id)
    assert all(any(d.status == "not_checked" for d in dev.details) for dev in saved.devices)
