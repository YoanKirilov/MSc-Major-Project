"""Component/task regressions from UI-01–28, using only synthetic saved reports.

The offline guard, fresh APP_DATA_DIR and rejected external browser requests protect
the user's reports and network. Navigation/editing must never launch a scan, AI
request or enrichment lookup. Geometry assertions intentionally inspect component
children: whole-document overflow checks alone missed the original defects.
"""

import json
import os
import re
import threading
import time
from pathlib import Path
from uuid import uuid4

import pytest
import uvicorn
from app.main import create_app
from app.risk.engine import evaluate_device
from app.schemas.scan import Device, DeviceDetail, ScanDocument, Service
from app.security.session import SessionManager
from app.storage.json_store import JsonStore
from tests.fixtures.browser import browser_listener

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in UI/UX browsers"),
]
VIEWPORTS = [(320, 568), (390, 844), (768, 1024), (1440, 1000)]
ENGINES = os.getenv("RESPONSIVE_BROWSERS", "chromium").split(",")


def _report(kind):
    """Deterministic facts, with variable IDs; no imported private scan evidence."""
    scan_id = str(uuid4())
    count = {"rich": 3, "many": 100, "zero": 1, "empty": 0, "failed": 0}[kind]
    devices, services, findings, targets = [], [], [], []
    for index in range(count):
        device_id = str(uuid4())
        ip = f"192.168.56.{index + 10}"
        device = Device(
            device_id=device_id,
            scan_id=scan_id,
            ip=ip,
            hostname=(
                "VeryLongReportedDeviceNameWithoutSpaces" * 3
                if kind == "rich" and index == 0
                else f"Example device {index + 1}"
                if index != 2
                else None
            ),
            hostname_source="reverse_dns" if index != 2 else None,
            hostname_observed_at="2026-10-08T09:00:00Z" if index != 2 else None,
            mac=f"02:00:00:00:00:{index:02x}",
            vendor="Example manufacturer" if kind == "rich" and index == 0 else None,
            discovery_method="known_host",
            reachability="observed",
        )
        devices.append(device)
        targets.append({"ip": ip, "service_status": "completed", "discovery_status": "observed"})
        if kind != "rich" or index != 0:
            continue
        device.hostname_conflict = True
        device.name_candidates = [
            {"name": "Advertised room display", "source": "mdns", "confidence": "low"}
        ]
        device.details = [
            DeviceDetail(
                kind="history",
                label="Earlier observations",
                value="Synthetic comparison: one earlier web feature was not observed this time.",
                source="saved reports",
                status="inferred",
            ),
            DeviceDetail(
                kind="mdns",
                label="Reported model",
                value="Example Model 200",
                source="mDNS",
                status="advertised",
            ),
            DeviceDetail(
                kind="web",
                label="Device page title",
                value="Example device administration",
                source="HTTP",
                status="observed",
            ),
        ]
        for port, name in [
            (21, "ftp"),
            (23, "telnet"),
            (80, "http"),
            (135, "msrpc"),
            (139, "netbios-ssn"),
            (443, "https"),
            (445, "microsoft-ds"),
            (554, "rtsp"),
            (902, "vmware-auth"),
            (912, "vmware-auth"),
            (3389, "ms-wbt-server"),
            (5357, "http"),
            (8443, "https-alt"),
        ]:
            services.append(
                Service(
                    service_id=str(uuid4()),
                    device_id=device_id,
                    port=port,
                    state="open",
                    name=name,
                    detection_method="probed",
                    nmap_confidence=9,
                )
            )
        findings.extend(evaluate_device(device, services))
    failed = kind in {"rich", "failed"}
    if failed:
        targets.append(
            {
                "ip": "192.168.56.231",
                "service_status": "failed",
                "discovery_status": "observed",
                "reason_code": "host_unreachable",
                "attempts": 2,
            }
        )
    if kind == "rich":
        assert len(findings) >= 4
        assert any(len(finding.actions) > 1 for finding in findings)
        findings[0].severity = "medium"
    return ScanDocument(
        scan_id=scan_id,
        created_at="2026-10-08T09:00:00Z",
        finished_at="2026-10-08T09:01:00Z",
        state="partial" if failed else "completed",
        scan_outcome="partial" if failed else "completed",
        phase="finished",
        analysis_status="failed",
        analysis_error="Synthetic local model unavailable.",
        target={"mode": "discover", "cidr": "192.168.56.0/24"},
        policy={"profile": "light", "allowed_network": "192.168.56.0/24"},
        coverage={
            "candidate_count": count + int(failed),
            "discovered_count": count + int(failed),
            "service_attempted_count": count + int(failed),
            "service_completed_count": count,
            "service_failed_count": int(failed),
            "discovery_complete": True,
            "service_stage_complete": True,
            "targets": targets,
        },
        devices=devices,
        services=services,
        observations=(
            [
                {
                    "ip": "192.168.56.231",
                    "advertised_name": "Unchecked display announcement",
                    "service_type": "_airplay._tcp.local.",
                    "port": 7000,
                },
                {
                    "ip": "192.168.56.232",
                    "advertised_name": "Unmatched announcement",
                    "service_type": "_http._tcp.local.",
                    "port": 80,
                },
            ]
            if kind == "rich"
            else []
        ),
        findings=findings,
        errors=(
            [
                {
                    "code": "HOST_UNREACHABLE",
                    "message": "Device did not respond after two bounded attempts.",
                    "target_ip": "192.168.56.231",
                }
            ]
            if failed
            else []
        ),
    )


@pytest.fixture(params=ENGINES)
def ui(request, tmp_path, monkeypatch):
    from playwright.sync_api import expect, sync_playwright

    async def unavailable(self):
        return False

    async def forbidden(*args, **kwargs):
        raise AssertionError("UI/UX tests must never start scanners, providers or lookups")

    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    monkeypatch.setattr(
        "app.explanations.service.ExplanationService.provider_available", unavailable
    )
    monkeypatch.setattr("app.api.session.nmap_preflight", lambda config: (True, "synthetic"))
    monkeypatch.setattr("app.api.session.nmap_interface_choices", lambda config: [])
    monkeypatch.setattr("app.api.session.detect_private_network", lambda: "192.168.56.0/24")
    store = JsonStore(Path(os.environ["APP_DATA_DIR"]))
    reports = {kind: _report(kind) for kind in ("rich", "many", "zero", "empty", "failed")}
    original = {}
    for kind, report in reports.items():
        store._create_scan(report)
        path = store._scan_dir(report.scan_id) / "scan.json"
        original[kind] = (path, path.read_bytes())
    manager = SessionManager()
    listener = browser_listener()
    port = listener.getsockname()[1]
    monkeypatch.setenv("APP_PORT", str(port))
    app = create_app(session_manager=manager)
    server = uvicorn.Server(uvicorn.Config(app, log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    failures, forbidden_requests, external = [], [], []
    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started
        app.state.supervisor.process_runner = forbidden
        app.state.explanations.provider.generate = forbidden
        app.state.nvd.lookup = forbidden
        base = f"http://127.0.0.1:{port}"
        with sync_playwright() as playwright:
            browser = getattr(playwright, request.param).launch(headless=True)
            context = browser.new_context(reduced_motion="reduce")

            def guard(route):
                url = route.request.url
                if not url.startswith(base + "/"):
                    external.append(url)
                    route.abort()
                    return
                if route.request.method == "POST" and url != base + "/api/session":
                    forbidden_requests.append(url)
                    route.abort()
                    return
                route.continue_()

            context.route("**/*", guard)
            page = context.new_page()
            page.on("pageerror", lambda error: failures.append(str(error)))
            page.goto(manager.get_bootstrap_url(port))
            page.wait_for_function("sessionStorage.getItem('network-assessor-csrf') !== null")
            expect(page.locator("#scanLaunchButton")).to_be_enabled()
            page.wait_for_function("document.querySelector('#runningScans').dataset.snapshot")
            yield page, base, reports
            assert not failures, failures
            assert not forbidden_requests, forbidden_requests
            assert not external, external
            for path, evidence in original.values():
                assert path.read_bytes() == evidence, "Editing must not rewrite scan evidence"
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        listener.close()
        assert not thread.is_alive()


def _open(ui, kind="rich", size=(390, 844)):
    from playwright.sync_api import expect

    page, base, reports = ui
    page.set_viewport_size({"width": size[0], "height": size[1]})
    page.goto(base + f"/scans/{reports[kind].scan_id}")
    expect(page.locator("#report-content")).to_be_visible()
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    expect(page.locator("#device-search-count")).not_to_be_empty(timeout=15000)
    return page, reports[kind]


def test_repeat_review_device_filter_retains_all_facts_and_opens_links_outside_filter(ui):
    from playwright.sync_api import expect

    page, base, reports = ui
    report = reports["rich"].model_copy(deep=True)
    report.scan_id = str(uuid4())
    for device in report.devices:
        device.scan_id = report.scan_id
    other = report.devices[1]
    extra = Service(
        service_id=str(uuid4()),
        device_id=other.device_id,
        port=80,
        state="open",
        name="http",
        detection_method="probed",
        nmap_confidence=9,
    )
    report.services.append(extra)
    report.findings.extend(evaluate_device(other, [extra]))
    store = JsonStore(Path(os.environ["APP_DATA_DIR"]))
    store._create_scan(report)
    path = store._scan_dir(report.scan_id) / "scan.json"
    before = path.read_bytes()
    page.goto(base + f"/scans/{report.scan_id}")
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    device_count = page.locator(".device-summary-group").count()
    task_count = page.locator("#nextStepsList .review-task").count()
    control = page.get_by_label("Review items for", exact=True)
    expect(control.locator("option")).to_have_count(3)
    control.select_option(other.device_id)
    expect(page.locator("#findingsList .finding-card")).to_have_count(1)
    expect(page.locator("#resultsSummary")).to_contain_text("for the selected device")
    expect(page.locator(".device-summary-group")).to_have_count(device_count)
    expect(page.locator("#nextStepsList .review-task")).to_have_count(task_count)
    page.wait_for_function(
        """({scan, device}) => JSON.parse(sessionStorage.getItem(
            'netguard-report-view-v1:' + scan) || '{}').reviewDevice === device""",
        arg={"scan": report.scan_id, "device": other.device_id},
    )
    page.reload()
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    expect(control).to_have_value(other.device_id)
    expect(page.locator("#findingsList .finding-card")).to_have_count(1)
    first = page.locator(f'.device-summary-group[data-device-ip="{report.devices[0].ip}"]')
    first.locator(".device-summary > summary").click()
    first.locator(".device-review-links button").first.click()
    expect(control).to_have_value("all")
    expect(page.locator("#findingsList .finding-card")).to_have_count(len(report.findings))
    expect(page.locator("#detailPanel")).to_be_focused()
    assert path.read_bytes() == before
    _open(ui, kind="empty")
    expect(control).to_be_disabled()
    expect(control).to_have_value("all")


def test_repeat_collapsed_task_status_and_empty_filters_remain_honest(ui):
    from playwright.sync_api import expect

    page, report = _open(ui)
    checklist = page.locator("#nextStepsList .next-step-checklist").first
    heading = checklist.locator(":scope > summary")
    expect(heading).to_contain_text("2 to check")
    expect(checklist).not_to_have_attribute("open", "")
    expect(page.locator("#checklist-filter-count")).to_contain_text("tasks available")
    heading.click()
    controls = checklist.locator(".action-check select")
    controls.first.select_option("checked")
    expect(heading).to_contain_text("1 Checked")
    controls.nth(1).select_option("need_help")
    expect(heading).to_contain_text("1 need help")
    heading.click()
    expect(checklist).not_to_have_attribute("open", "")
    expect(heading).to_contain_text("1 Checked")
    page.locator("#checklist-filter").select_option("checked")
    expect(heading).to_contain_text("1 available in this filter")
    expect(page.locator("#expandReviewTasks")).to_be_enabled()
    page.locator("#checklist-filter").select_option("all")
    endpoint = f"**/api/live-scans/{report.scan_id}/annotations"
    page.route(endpoint, lambda route: route.fulfill(status=503, body='{"detail":"Test delay"}'))
    page.reload()
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    expect(heading).to_contain_text("saved status unavailable")
    expect(page.locator("#checklist-progress")).to_contain_text("unavailable")
    expect(controls.first).to_be_disabled()
    page.unroute(endpoint)
    # A fresh report has no Checked actions; no-match disclosure buttons must not
    # suggest that hidden rows can be expanded, or change task state.
    page, _ = _open(ui, kind="rich")
    page.locator("#checklist-filter").select_option("checked")
    # The rich report retains the saved Checked action from this test, so use a
    # separate fresh record to verify the zero-match case.
    fresh = _report("rich")
    JsonStore(Path(os.environ["APP_DATA_DIR"]))._create_scan(fresh)
    _, base, _ = ui
    page.goto(base + f"/scans/{fresh.scan_id}")
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    page.locator("#checklist-filter").select_option("checked")
    expect(page.locator("#checklist-empty")).to_be_visible()
    expect(page.locator("#expandReviewTasks")).to_be_disabled()
    expect(page.locator("#collapseReviewTasks")).to_be_disabled()
    page.locator("#checklist-filter").select_option("all")
    expect(page.locator("#expandReviewTasks")).to_be_enabled()


def test_repeat_technical_columns_and_unknown_reply_context_preserve_evidence(ui):
    from playwright.sync_api import expect

    page, base, reports = ui
    report = reports["rich"].model_copy(deep=True)
    report.scan_id = str(uuid4())
    for device in report.devices:
        device.scan_id = report.scan_id
    for service in report.services:
        service.name = "tcpwrapped"
    report.findings = evaluate_device(report.devices[0], report.services)
    store = JsonStore(Path(os.environ["APP_DATA_DIR"]))
    store._create_scan(report)
    path = store._scan_dir(report.scan_id) / "scan.json"
    before = path.read_bytes()
    for width in (320, 390, 768, 1440):
        page.set_viewport_size({"width": width, "height": 1000})
        page.goto(base + f"/scans/{report.scan_id}")
        expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
        table = page.locator("#technical-devices")
        if not table.evaluate("el => el.open"):
            table.locator(":scope > summary").click()
        for summary in table.locator("tbody summary").all():
            rect = summary.bounding_box()
            assert rect["width"] >= 110 and rect["height"] >= 44
        wrapper = table.locator(".device-table-wrap")
        if width <= 768:
            assert wrapper.evaluate("el => el.scrollWidth > el.clientWidth")
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
        expect(page.locator("#repeated-replies-note")).to_contain_text(
            "not confirmed software problems"
        )
        expect(page.locator("#findingsList .finding-card")).to_have_count(len(report.findings))
        assert page.locator("#nextStepsList .review-task").count() == sum(
            len(finding.actions) for finding in report.findings
        )
    page.locator("#searchInput").fill("nothing should match")
    expect(page.locator("#repeated-replies-note")).to_be_hidden()
    assert path.read_bytes() == before


def test_final_layout_supporting_options_reflow_and_keep_native_keyboard_state(ui):
    from playwright.sync_api import expect

    page, _ = _open(ui, size=(1440, 1000))
    grid = page.locator(".supporting-grid")
    summaries = grid.locator(":scope > details > summary, :scope > section > details > summary")
    cards = grid.locator(":scope > *:visible")
    assert cards.count() == 6  # Includes the optional unmatched mDNS announcements.
    tops = [card.bounding_box()["y"] for card in cards.all()]
    assert max(tops) - min(tops) <= 1
    for selector in ("main", ".topbar", ".site-footer"):
        assert page.locator(selector).bounding_box()["width"] == 1360
    expect(page.locator("#resultsSummary")).to_have_attribute("role", "status")
    expect(page.locator("#resultsSummary")).to_have_attribute("aria-atomic", "true")
    glossary = page.locator("#report-glossary")
    summary = glossary.locator(":scope > summary")
    summary.focus()
    page.keyboard.press("Enter")
    expect(glossary).to_have_attribute("open", "")
    assert abs(glossary.bounding_box()["width"] - grid.bounding_box()["width"]) <= 1
    expect(summary).to_be_focused()
    page.reload()
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    expect(glossary).to_have_attribute("open", "")
    for width in (320, 390, 768):
        page.set_viewport_size({"width": width, "height": 1000})
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
        for control in summaries.all():
            rect = control.bounding_box()
            assert rect["width"] >= 44 and rect["height"] >= 44
    page.set_viewport_size({"width": 768, "height": 1024})
    page.add_style_tag(content="html {font-size:200% !important}")
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    expect(summary).to_be_visible()
    expect(page.locator("#textAlignment")).to_have_count(0)
    expect(page.locator("#themePreference")).to_have_count(1)


def test_final_layout_renders_only_current_wording_without_changing_saved_rules(ui):
    from playwright.sync_api import expect

    page, base, reports = ui
    report = reports["rich"]
    endpoint = base + f"/api/live-scans/{report.scan_id}"
    before = page.request.get(endpoint).json()
    page, _ = _open(ui)
    for card in page.locator("#findingsList .finding-card").all():
        card.click()
        expect(page.locator("#detailPanel")).to_contain_text("What we found")
        expect(page.locator("#detailPanel")).to_contain_text("What to do next")
        expect(page.locator("#detailPanel")).not_to_contain_text("Original rule-based")
        expect(page.locator("#detailPanel")).not_to_contain_text("Guidance saved before")
        expect(page.locator("#detailPanel .supporting-details > summary")).to_have_text(
            "Sources and technical details"
        )
    after = page.request.get(endpoint).json()
    assert before["findings"] == after["findings"]
    assert before["guidance_history"] == after["guidance_history"]
    assert before["explanations"] == after["explanations"]
    assert all(finding["fixed_explanation"] for finding in after["findings"])
    _open(ui, kind="empty")
    expect(page.locator("#checklist-filter-count")).to_contain_text("No review tasks were recorded")
    expect(page.locator("#expandReviewTasks")).to_be_disabled()


def test_reading_followup_grouped_evidence_and_theme_survive_reload(ui):
    from playwright.sync_api import expect

    page, report = _open(ui)
    group = page.locator(f'.device-summary-group[data-device-ip="{report.devices[0].ip}"]')
    group.locator(".device-summary > summary").click()
    features = group.locator(".device-info-disclosures > .feature-technical")
    expect(features).to_have_count(1)
    expect(group.locator(".device-feature details")).to_have_count(0)
    features.locator(":scope > summary").click()
    expected = [
        s
        for s in report.services
        if s.device_id == report.devices[0].device_id and s.state == "open"
    ]
    expect(features.locator(".feature-evidence")).to_have_count(len(expected))
    for service in expected:
        expect(features).to_contain_text(str(service.port))
        if service.product:
            expect(features).to_contain_text(service.product)
    assert features.locator("p").first.evaluate("el => getComputedStyle(el).textAlign") == "left"
    assert (
        page.locator("#detailPanel .detail-block p").first.evaluate(
            "el => getComputedStyle(el).textAlign"
        )
        == "left"
    )
    page.locator(".reading-options > summary").click()
    page.locator("#themePreference").select_option("light")
    page.reload()
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    expect(page.locator("#themePreference")).to_have_value("light")
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    expect(group.locator(".feature-technical")).to_have_attribute("open", "")
    assert (
        page.locator("#detailPanel .detail-block p").first.evaluate(
            "el => getComputedStyle(el).textAlign"
        )
        == "left"
    )
    page.locator("#themePreference").select_option("dark")
    for width, height in VIEWPORTS:
        page.set_viewport_size({"width": width, "height": height})
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")


def test_reading_followup_exact_device_search_and_recognition_never_match_prefixes(ui):
    from playwright.sync_api import expect

    page, base, reports = ui
    report = reports["rich"]
    endpoint = base + f"/api/live-scans/{report.scan_id}"
    payload = page.request.get(endpoint).json()
    address = payload["devices"][0]["ip"]
    payload["devices"][1]["ip"] = address + "0"  # .10 must not match .100.
    payload["devices"][2]["hostname"] = address  # A name is not the device address.
    page.route(
        endpoint,
        lambda route: route.fulfill(content_type="application/json", body=json.dumps(payload)),
    )
    _open(ui)
    page.locator("#deviceSearchInput").fill(address)
    expect(page.locator("#device-summaries .device-summary-group")).to_have_count(1)
    expect(page.locator("#device-summaries .device-summary-address")).to_contain_text(address)
    page.reload()
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    expect(page.locator("#device-summaries .device-summary-group")).to_have_count(1)
    page.locator("#clearDeviceSearch").click()
    page.locator("#identifyFirstDevice").click()
    expect(page.locator("#device-summaries .device-summary-group")).to_have_count(1)
    page.locator("#clearDeviceSearch").click()
    page.locator("#deviceSearchInput").fill("192.168.56.")
    expect(page.locator("#device-summaries .device-summary-group")).to_have_count(4)
    page.locator("#deviceSearchInput").fill("192.168.56.254")
    expect(page.locator("#device-summaries .device-summary-group")).to_have_count(0)


def test_reading_followup_failed_preview_and_first_action_caution_are_explicit(ui):
    from playwright.sync_api import expect

    page, _ = _open(ui)
    preview = page.locator(
        '.device-summary-group[data-device-ip="192.168.56.231"] .device-summary-preview'
    )
    expect(preview).to_contain_text("not assessed")
    expect(preview).not_to_contain_text("0 observed")
    # Select a recorded web item for the summary without changing evidence.
    _, base, reports = ui
    original = page.request.get(base + f"/api/live-scans/{reports['rich'].scan_id}").json()
    original["findings"] = [f for f in original["findings"] if f["rule_id"] == "R03"]
    endpoint = base + f"/api/live-scans/{reports['rich'].scan_id}"
    page.route(
        endpoint,
        lambda route: route.fulfill(content_type="application/json", body=json.dumps(original)),
    )
    page.reload()
    expect(page.locator("#first-action-precaution")).to_be_visible()
    expect(page.locator("#first-action-precaution")).to_contain_text("Do not enter passwords")
    group = page.locator(".device-summary-group").first
    group.locator(".device-summary > summary").click()
    group.locator("[data-glossary-link]").click()
    expect(page.locator("#report-glossary")).to_have_attribute("open", "")
    expect(page.locator("#report-glossary > summary")).to_be_focused()


@pytest.mark.parametrize("size", VIEWPORTS)
def test_checklist_and_search_children_belong_inside_their_components(ui, size):
    """UI-01/04/05: don't mistake no page overflow for correct component geometry."""
    from playwright.sync_api import expect

    page, _ = _open(ui, size=size)
    checks = page.locator("#detailPanel .action-check")
    expect(checks.first).to_be_visible()
    for row in checks.all():
        item = row.locator("xpath=ancestor::li[1]")
        row_box, item_box = row.bounding_box(), item.bounding_box()
        assert row_box["width"] > item_box["width"] * 0.65, (size, row_box, item_box)
        assert row_box["x"] >= item_box["x"] + 20
        assert row_box["x"] + row_box["width"] <= item_box["x"] + item_box["width"] + 1
        select = row.locator("select").bounding_box()
        assert select["x"] >= row_box["x"] - 1
        assert select["x"] + select["width"] <= row_box["x"] + row_box["width"] + 1
    page.locator("#searchInput").fill("192.168.56.10")
    search = page.locator("#searchInput").locator(
        "xpath=ancestor::*[contains(@class, 'search-box')][1]"
    )
    clear = page.locator("#clearSearchButton")
    outer, inner = search.bounding_box(), clear.bounding_box()
    assert inner["y"] >= outer["y"] - 1
    assert inner["y"] + inner["height"] <= outer["y"] + outer["height"] + 1
    assert inner["x"] + inner["width"] <= outer["x"] + outer["width"] + 1
    clear.click()
    expect(page.locator("#searchInput")).to_have_value("")
    expect(page.locator("#searchInput")).to_be_focused()
    for badge in page.locator("#findingsList .severity-badge").all():
        lines = badge.evaluate("""element => {
            const range = document.createRange(); range.selectNodeContents(element);
            return [...range.getClientRects()].map(rect => Math.round(rect.top));
        }""")
        assert len(set(lines)) == 1, (size, badge.inner_text(), lines)
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")


@pytest.mark.parametrize("size", VIEWPORTS)
def test_selecting_a_result_keeps_focus_and_places_mobile_explanation_nearby(ui, size):
    """UI-02/03/26: selection is stable and the revealed result isn't below the list."""
    from playwright.sync_api import expect

    page, _ = _open(ui, size=size)
    selected = page.locator("#findingsList .finding-card").nth(1)
    selected.focus()
    identity = selected.get_attribute("data-finding-id") or selected.inner_text()
    page.keyboard.press("Enter")
    expect(selected).to_be_focused()
    expect(selected).to_have_attribute("aria-pressed", "true")
    outline = selected.evaluate("""element => {
        const style = getComputedStyle(element);
        return {style:style.outlineStyle, width:parseFloat(style.outlineWidth)};
    }""")
    assert outline["style"] != "none" and outline["width"] >= 2, outline
    assert (selected.get_attribute("data-finding-id") or selected.inner_text()) == identity
    expect(page.locator("#detailPanel")).to_be_visible()
    if size[0] < 880:
        # Sample both boxes in one frame. Firefox's asynchronous scroll movement
        # can otherwise occur between two separate browser protocol calls.
        trigger, detail = selected.evaluate("""element => {
            const trigger = element.getBoundingClientRect();
            const detail = document.querySelector('#detailPanel').getBoundingClientRect();
            return [trigger, detail].map(rect => ({x:rect.x, y:rect.y,
                width:rect.width, height:rect.height}));
        }""")
        assert 0 <= detail["y"] - (trigger["y"] + trigger["height"]) <= 32, (
            size,
            trigger,
            detail,
        )
        assert abs(detail["x"] - trigger["x"]) <= 12
    assert page.locator("#findingsList").get_attribute("aria-live") is None
    assert page.locator("#detailPanel").get_attribute("aria-live") is None
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement !== document.body")


def test_changing_between_mobile_and_desktop_preserves_selected_result_node(ui):
    """UI-02/03/28: moving a pane must not recreate the user's selected trigger."""
    from playwright.sync_api import expect

    page, _ = _open(ui)
    selected = page.locator("#findingsList .finding-card").nth(2)
    selected.focus()
    page.keyboard.press("Enter")
    selected.evaluate("element => { window.uiSelectedTrigger = element; }")
    for width, height in [(1440, 1000), (320, 568), (768, 1024), (390, 844)]:
        page.set_viewport_size({"width": width, "height": height})
        expect(selected).to_have_attribute("aria-pressed", "true")
        expect(selected).to_be_focused()
        assert selected.evaluate("element => element === window.uiSelectedTrigger")
        page.wait_for_function(
            """compact => {
                const panel = document.querySelector('#detailPanel');
                const list = document.querySelector('#findingsList');
                return compact ? list.contains(panel) : !list.contains(panel);
            }""",
            arg=width < 880,
        )
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")


def test_device_anatomy_keeps_addresses_identity_and_all_features_locally_accessible(ui):
    """UI-07/09/10/11: sparse, unknown and failed cards don't need a technical table."""
    from playwright.sync_api import expect

    page, report = _open(ui)
    groups = page.locator("#device-summaries .device-summary-group")
    expect(groups).to_have_count(4)
    expected_ips = {device.ip for device in report.devices} | {"192.168.56.231"}
    displayed_ips = set()
    for group in groups.all():
        card = group.locator(":scope > details.device-summary")
        identity = card.locator(":scope > summary").inner_text()
        matched = [ip for ip in expected_ips if ip in identity]
        assert len(matched) == 1, identity
        displayed_ips.update(matched)
        expect(card).not_to_have_attribute("open", "")
        button = group.locator("[data-nickname-device]")
        if button.count():
            outer, action = group.bounding_box(), button.bounding_box()
            assert outer["y"] <= action["y"]
            assert action["y"] + action["height"] <= outer["y"] + outer["height"] + 1
            assert "primary-button" not in (button.get_attribute("class") or "")
        card.locator(":scope > summary").click()
    assert displayed_ips == expected_ips
    rich = groups.filter(
        has=page.locator(f'[data-nickname-device="{report.devices[0].device_id}"]')
    )
    rich.get_by_text("About this device", exact=True).click()
    rich.get_by_text("Reported model and additional observations", exact=True).click()
    expect(rich.get_by_text("Example manufacturer", exact=False)).to_be_visible()
    expect(rich.get_by_text("Example Model 200", exact=False)).to_be_visible()
    expect(rich).to_contain_text("mDNS")
    expect(rich).to_contain_text("unverified")
    # Displaying every feature in the expanded device is also valid; no extra
    # Show-all button is necessary when there is no silent five-feature cutoff.
    expect(rich.locator(".device-features .device-feature")).to_have_count(13)
    for service in report.services:
        expect(
            rich.locator(".device-feature-context").filter(
                has_text=re.compile(rf"\b{service.port}\b")
            )
        ).to_be_visible()
    expect(page.locator("#technical-devices")).not_to_have_attribute("open", "")


def test_complete_checklist_exposes_every_counted_action_and_shared_status(ui):
    """UI-17/18: a reported task total must have a discoverable complete task list."""
    from playwright.sync_api import expect

    page, report = _open(ui)
    for summary in page.locator("#nextStepsList .next-step-checklist > summary").all():
        summary.click()
    expected = {
        (finding.finding_id, action.action_id)
        for finding in report.findings
        for action in finding.actions
    }
    controls = page.locator("#nextStepsList .action-check select")
    seen = {
        (control.get_attribute("data-finding-id"), control.get_attribute("data-action-id"))
        for control in controls.all()
    }
    assert seen == expected
    expect(page.locator("#checklist-progress")).to_contain_text(f"of {len(expected)} actions")
    select = controls.first
    finding_id, action_id = (
        select.get_attribute("data-finding-id"),
        select.get_attribute("data-action-id"),
    )
    select.select_option("need_help")
    expect(page.locator("#checklist-notice")).to_contain_text("saved")
    matches = page.locator(
        f'.action-check select[data-finding-id="{finding_id}"][data-action-id="{action_id}"]'
    )
    for match in matches.all():
        expect(match).to_have_value("need_help")
    page.locator("#checklist-filter").select_option("need_help")
    expect(select).to_be_visible()
    expect(page.locator("#checklist-progress")).to_contain_text("1 need help")


def test_searches_are_explicit_and_devices_without_findings_remain_searchable(ui):
    """UI-19: the findings search must not silently filter the device list."""
    from playwright.sync_api import expect

    page, _ = _open(ui)
    expect(page.get_by_label("Search review items", exact=True)).to_have_attribute(
        "id", "searchInput"
    )
    expect(page.get_by_label("Search devices", exact=True)).to_have_attribute(
        "id", "deviceSearchInput"
    )
    page.locator("#searchInput").fill("no review result should match")
    expect(page.locator("#findingsList")).to_contain_text("No review items match")
    expect(page.locator("#device-summaries .device-summary-group")).to_have_count(4)
    page.locator("#deviceSearchInput").fill("192.168.56.11")
    expect(page.locator("#device-summaries .device-summary-group")).to_have_count(1)
    expect(page.locator("#device-summaries summary").first).to_contain_text("192.168.56.11")
    expect(page.locator("#device-search-count")).to_contain_text("Showing 1")
    expect(page.locator("#device-search-count")).to_contain_text("4 recorded in total")
    page.locator("#clearSearchButton").click()
    expect(page.locator("#deviceSearchInput")).to_have_value("192.168.56.11")
    expect(page.locator("#findingsList .finding-card").first).to_be_visible()


def test_contextual_edit_dialog_cancel_save_and_focus_return(ui):
    """UI-24: native prompts are replaced by labelled, revision-safe local editors."""
    from playwright.sync_api import expect

    page, _ = _open(ui)
    native_dialogs = []
    page.on("dialog", lambda dialog: (native_dialogs.append(dialog.type), dialog.dismiss()))
    nickname = page.locator("#device-summaries [data-nickname-device]").first
    nickname.click()
    dialog = page.locator("#annotationEditorDialog")
    expect(dialog).to_be_visible()
    expect(dialog).to_have_attribute("aria-labelledby", "annotationEditorTitle")
    expect(page.locator("#annotationEditorInput")).to_be_focused()
    page.keyboard.press("Shift+Tab")
    assert dialog.evaluate("element => element.contains(document.activeElement)")
    page.keyboard.press("Tab")
    assert dialog.evaluate("element => element.contains(document.activeElement)")
    page.locator("#annotationEditorInput").fill("Example room display")
    page.keyboard.press("Escape")
    expect(dialog).not_to_be_visible()
    expect(nickname).to_be_focused()
    nickname.click()
    page.locator("#annotationEditorInput").fill("Example room display")
    page.locator("#annotationEditorSave").click()
    expect(dialog).not_to_be_visible()
    expect(page.locator("#device-summaries summary").first).to_contain_text("Example room display")
    expect(page.locator("#device-summaries [data-nickname-device]").first).to_be_focused()
    page.locator("#editReportTitle").click()
    expect(dialog).to_be_visible()
    expect(page.locator("#annotationEditorInput")).to_have_attribute("maxlength", "100")
    page.locator("#annotationEditorInput").fill("Review the example room display")
    page.locator("#annotationEditorSave").click()
    expect(dialog).not_to_be_visible()
    expect(page.locator("#report-user-title")).to_have_text("Review the example room display")
    expect(page.locator("#editReportTitle")).to_be_focused()
    assert not native_dialogs
    page.reload()
    expect(page.locator("#report-user-title")).to_have_text("Review the example room display")
    expect(page.locator("#device-summaries summary").first).to_contain_text("Example room display")


def test_edit_conflict_keeps_input_and_reports_the_error_inside_the_dialog(ui):
    """UI-24/25: another tab's revision must not silently replace the user's edit."""
    from playwright.sync_api import expect

    page, report = _open(ui)
    base = ui[1]
    endpoint = base + f"/api/live-scans/{report.scan_id}/title"
    writes = []

    def conflict(route):
        writes.append(route.request.post_data_json)
        route.fulfill(
            status=409,
            content_type="application/json",
            body='{"detail":"Saved notes changed in another tab. Review them before saving."}',
        )

    page.route(endpoint, conflict)
    page.locator("#editReportTitle").click()
    page.locator("#annotationEditorInput").fill("Preserve this unsaved title")
    page.locator("#annotationEditorSave").click()
    expect(page.locator("#annotationEditorStatus")).to_contain_text("not saved")
    expect(page.locator("#annotationEditorDialog")).to_be_visible()
    expect(page.locator("#annotationEditorInput")).to_have_value("Preserve this unsaved title")
    assert len(writes) == 1
    assert writes[0]["expected_revision"] == 1
    page.locator("#annotationEditorCancel").click()
    expect(page.locator("#editReportTitle")).to_be_focused()


def test_renaming_a_filtered_device_restores_focus_to_its_search_when_it_disappears(ui):
    """UI-24/28: rename may remove the trigger without losing the user's position."""
    from playwright.sync_api import expect

    page, _ = _open(ui)
    nickname = page.locator("#device-summaries [data-nickname-device]").first
    nickname.click()
    page.locator("#annotationEditorInput").fill("Temporary matching nickname")
    page.locator("#annotationEditorSave").click()
    expect(page.locator("#annotationEditorDialog")).not_to_be_visible()
    page.locator("#deviceSearchInput").fill("Temporary matching nickname")
    expect(page.locator("#device-summaries .device-summary-group")).to_have_count(1)
    page.locator("#device-summaries [data-nickname-device]").first.click()
    page.locator("#annotationEditorInput").fill("Different saved name")
    page.locator("#annotationEditorSave").click()
    expect(page.locator("#annotationEditorDialog")).not_to_be_visible()
    expect(page.locator("#device-summaries .device-summary-group")).to_have_count(0)
    expect(page.locator("#deviceSearchInput")).to_be_focused()
    expect(page.locator("#deviceSearchInput")).to_have_value("Temporary matching nickname")
    page.locator("#clearDeviceSearch").click()
    expect(page.locator("#device-summaries .device-summary-group")).to_have_count(4)
    expect(page.locator("#device-summaries summary").first).to_contain_text("Different saved name")


def test_disclosure_targets_and_user_text_spacing_keep_components_usable(ui):
    """UI-06/26: check real target rectangles and user-specified text spacing."""
    page, _ = _open(ui, size=(320, 568))
    for summary in page.locator("main summary").all():
        if summary.is_visible():
            target = summary.bounding_box()
            # This app adopts padded disclosure rows, not the inline-text exception.
            assert target["height"] >= 24, (summary.inner_text(), target)
    page.add_style_tag(
        content="""p { margin-block-end: 2em !important; }
        body { line-height: 1.5 !important; letter-spacing: .12em !important;
               word-spacing: .16em !important; }
        input, button, select, textarea { letter-spacing: .12em !important;
                                         word-spacing: .16em !important; }"""
    )
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    page.locator("#searchInput").fill("file")
    clear = page.locator("#clearSearchButton").bounding_box()
    search = (
        page.locator("#searchInput")
        .locator("xpath=ancestor::*[contains(@class, 'search-box')][1]")
        .bounding_box()
    )
    assert clear["x"] + clear["width"] <= search["x"] + search["width"] + 1
    assert clear["y"] + clear["height"] <= search["y"] + search["height"] + 1


def test_all_pages_share_navigation_and_keyboard_bypass(ui):
    """UI-22/26: current page and a meaningful main heading, no shell islands."""
    from playwright.sync_api import expect

    page, base, reports = ui
    for route in (
        "/",
        "/light",
        "/deep",
        "/settings",
        "/history",
        f"/scans/{reports['rich'].scan_id}",
    ):
        page.goto(base + route)
        expect(page.get_by_role("link", name="Skip to main content", exact=True)).to_have_attribute(
            "href", "#main-content"
        )
        expect(page.locator("main#main-content")).to_have_count(1)
        expect(
            page.get_by_role("banner").get_by_role("link", name="NetGuard AI", exact=False)
        ).to_be_visible()
        expect(page.get_by_role("navigation", name="Main navigation")).to_be_visible()
        expect(page.locator("main h1")).to_have_count(1)
        assert "NetGuard" in page.title()
        # Explicit tabindex=0 keeps the bypass in the normal keyboard sequence
        # even when the browser's default link-tabbing preference excludes links.
        page.keyboard.press("Tab")
        skip = page.get_by_role("link", name="Skip to main content", exact=True)
        expect(skip).to_be_focused()
        page.keyboard.press("Enter")
        expect(page.locator("#main-content")).to_be_focused()
        if route in ("/", "/light", "/deep"):
            expect(page.locator("#scanLaunchButton")).to_be_enabled()
            page.wait_for_function("document.querySelector('#runningScans').dataset.snapshot")
            if route == "/deep":
                expect(page.locator("#recentDeviceNote")).not_to_be_empty()
        elif route == "/settings":
            expect(page.locator("#save-settings")).to_be_enabled()
        elif route == "/history":
            expect(page.locator("#history-list")).not_to_have_attribute("aria-busy", "true")
        else:
            expect(page.locator("#device-search-count")).not_to_be_empty()


def test_many_devices_are_compact_but_every_device_can_be_found(ui):
    """UI-27: bounded initial density is an explicit view, never a data cutoff."""
    from playwright.sync_api import expect

    page, report = _open(ui, kind="many", size=(768, 1024))
    groups = page.locator("#device-summaries .device-summary-group")
    assert 0 < groups.count() < len(report.devices)
    for card in groups.locator(":scope > details.device-summary").all():
        expect(card).not_to_have_attribute("open", "")
    expect(page.locator("#deviceSort")).to_be_visible()
    expect(page.locator("#showMoreDevices")).to_be_visible()
    while page.locator("#showMoreDevices").is_visible():
        page.locator("#showMoreDevices").click()
    expect(groups).to_have_count(100)
    page.locator("#deviceSearchInput").fill(report.devices[-1].ip)
    expect(groups).to_have_count(1)
    expect(groups.first.locator(".device-summary > summary")).to_contain_text(report.devices[-1].ip)
    expect(page.locator("#device-search-count")).to_contain_text("Showing 1")
    expect(page.locator("#device-search-count")).to_contain_text("100 recorded in total")


@pytest.mark.parametrize("kind", ["zero", "empty", "failed"])
def test_zero_empty_and_failed_reports_keep_evidence_distinct_from_ai_outage(ui, kind):
    """UI-25: a missing AI/model or check is not a zero-findings safety verdict."""
    from playwright.sync_api import expect

    page, report = _open(ui, kind=kind, size=(320, 568))
    expect(page.locator("#report-content")).to_be_visible()
    expect(page.locator("#ai-report-notice")).to_be_visible()
    expect(page.locator("#ai-report-notice")).to_contain_text("unavailable")
    expect(page.locator("#simplifyButton")).to_be_visible()
    expect(page.locator("#findingsList")).not_to_be_empty()
    if kind == "failed":
        expect(page.locator("#scan-problems")).to_be_visible()
        expect(page.locator("#device-summaries")).to_contain_text("192.168.56.231")
        expect(page.locator("#retryHostsButton")).to_be_visible()
        assert report.coverage.service_completed_count == 0
    elif kind == "empty":
        expect(page.locator("#device-search-count")).to_contain_text("0")
    else:
        expect(page.locator("#device-summaries summary").first).to_contain_text(
            report.devices[0].ip
        )
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")


def test_followup_loading_waits_for_facts_and_retry_preserves_honest_counts(ui):
    """Unknown observations must not look like zero checked devices or a clean report."""
    from playwright.sync_api import expect

    page, base, reports = ui
    endpoint = base + f"/api/live-scans/{reports['zero'].scan_id}"
    page.route(endpoint, lambda route: route.fulfill(status=503, body='{"detail":"Test delay"}'))
    page.goto(base + f"/scans/{reports['zero'].scan_id}")
    expect(page.locator("#retryReportLoad")).to_be_visible()
    for selector in ("#device-metric", "#service-metric", "#result-count"):
        expect(page.locator(selector)).to_have_text("—")
    expect(page.locator("#report-content")).not_to_be_visible()
    expect(page.locator("#report-content")).to_have_attribute("aria-busy", "false")
    page.unroute(endpoint)
    page.locator("#retryReportLoad").click()
    expect(page.locator("#report-content")).to_be_visible()
    expect(page.locator("#device-metric")).to_have_text("1 of 1 discovered")
    expect(page.locator("#service-metric")).to_have_text("0")
    expect(page.locator("#findingsList")).to_contain_text("not fully assessed")


def test_followup_titles_are_consistent_and_buttons_use_valid_phrasing_content(ui):
    from playwright.sync_api import expect

    page, report = _open(ui, size=(1440, 1000))
    group = page.locator(".device-summary-group").filter(
        has=page.locator(f'[data-nickname-device="{report.devices[0].device_id}"]')
    )
    group.locator(".device-summary > summary").click()
    titles = []
    for card in page.locator("#findingsList .finding-card").all():
        identity = card.get_attribute("data-finding-id")
        label = card.locator(".finding-title").inner_text()
        titles.append(label)
        expect(card.locator("h3, p, div, button, a, input, select")).to_have_count(0)
        expect(
            group.locator(f'.device-review-links [data-finding-id="{identity}"]')
        ).to_contain_text(label)
        task = page.locator(f'.next-step-checklist[data-finding-id="{identity}"]')
        expect(task.locator("..").locator(":scope > strong")).to_have_text(label)
        card.click()
        expect(page.locator("#detailPanel > h3")).to_have_text(label)
    assert len(set(titles)) == len(titles)
    assert any("Windows communication" in title for title in titles)


def test_followup_comparisons_and_unfinished_device_announcements_have_one_home(ui):
    from playwright.sync_api import expect

    page, _ = _open(ui)
    rich = page.locator('.device-summary-group[data-device-ip="192.168.56.10"]')
    rich.locator(".device-summary > summary").click()
    rich.get_by_text("About this device", exact=True).click()
    rich.get_by_text("Comparison with earlier observations", exact=True).click()
    expect(rich).to_contain_text("one earlier web feature was not observed")
    expect(page.locator("#comparison-list")).to_have_count(0)
    unchecked = page.locator('.device-summary-group[data-device-ip="192.168.56.231"]')
    unchecked.locator(".device-summary > summary").click()
    unchecked.get_by_text("About this device", exact=True).click()
    unchecked.get_by_text("Device announcements (1)", exact=True).click()
    expect(unchecked).to_contain_text("Unchecked display announcement")
    expect(unchecked).to_contain_text("unverified claim")
    expect(unchecked).to_contain_text("checks could not finish")
    page.locator("#report-comparisons > summary").click()
    expect(page.locator("#mdns-list")).not_to_contain_text("Unchecked display announcement")
    expect(page.locator("#mdns-list")).to_contain_text("Unmatched announcement")


def test_followup_refresh_restores_filters_selection_disclosures_and_scroll_without_new_requests(
    ui,
):
    from playwright.sync_api import expect

    page, report = _open(ui, size=(768, 1024))
    # Keep a stale section fragment: refreshing later must restore the actual
    # reading position, not jump back to the last navigation link used.
    page.get_by_role("link", name="Devices", exact=True).click()
    page.locator("#deviceSearchInput").fill("192.168.56.10")
    page.locator("#deviceSort").select_option("name")
    device = page.locator(".device-summary-group .device-summary")
    device.locator(":scope > summary").click()
    device.get_by_text("About this device", exact=True).click()
    page.locator("#searchInput").fill("192.168.56.10")
    page.locator('.filter-chip[data-filter="informational"]').click()
    selected = page.locator("#findingsList .finding-card").nth(1)
    identity = selected.get_attribute("data-finding-id")
    selected.click()
    page.locator("#expandReviewTasks").click()
    page.locator("#next-title").evaluate("element => element.scrollIntoView({block:'start'})")
    key = "netguard-report-view-v1:" + report.scan_id
    page.wait_for_function(
        """key => { const state = JSON.parse(sessionStorage.getItem(key) || '{}');
            return state.y > 0 && Math.abs(state.y - scrollY) < 2 && state.open?.length > 0; }""",
        arg=key,
    )
    before = page.evaluate("key => JSON.parse(sessionStorage.getItem(key))", key)
    page.reload()
    expect(page.locator("#report-content")).to_be_visible()
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    expect(page.locator("#deviceSearchInput")).to_have_value("192.168.56.10")
    expect(page.locator("#deviceSort")).to_have_value("name")
    expect(page.locator("#searchInput")).to_have_value("192.168.56.10")
    expect(page.locator('.filter-chip[data-filter="informational"]')).to_have_attribute(
        "aria-pressed", "true"
    )
    expect(
        page.locator(f'#findingsList .finding-card[data-finding-id="{identity}"]')
    ).to_have_attribute("aria-pressed", "true")
    expect(device).to_have_attribute("open", "")
    expect(device.get_by_text("About this device", exact=True).locator("..")).to_have_attribute(
        "open", ""
    )
    for task in page.locator(".next-step-checklist").all():
        expect(task).to_have_attribute("open", "")
    page.wait_for_function("y => Math.abs(scrollY - y) < 5", arg=before["y"])
    # A different saved report in this same tab has separate reading state.
    _open(ui, kind="zero")
    expect(page.locator("#deviceSearchInput")).to_have_value("")
    expect(page.locator("#searchInput")).to_have_value("")
    expect(page.locator('.filter-chip[data-filter="all"]')).to_have_attribute(
        "aria-pressed", "true"
    )


def test_followup_collapsing_all_tasks_is_reading_state_not_editing_or_scanning(ui):
    from playwright.sync_api import expect

    page, _ = _open(ui)
    page.locator("#checklist-filter").select_option("to_check")
    page.locator("#expandReviewTasks").click()
    for task in page.locator(".next-step-checklist").all():
        expect(task).to_have_attribute("open", "")
    page.locator("#collapseReviewTasks").focus()
    page.keyboard.press("Enter")
    expect(page.locator("#collapseReviewTasks")).to_be_focused()
    for task in page.locator(".next-step-checklist").all():
        expect(task).not_to_have_attribute("open", "")
    page.reload()
    expect(page.locator("#report-content")).to_be_visible()
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    expect(page.locator("#checklist-filter")).to_have_value("to_check")
    for task in page.locator(".next-step-checklist").all():
        expect(task).not_to_have_attribute("open", "")
    _open(ui, kind="empty")
    expect(page.locator("#expandReviewTasks")).to_be_disabled()
    expect(page.locator("#collapseReviewTasks")).to_be_disabled()


def test_followup_navigation_does_not_obscure_targets_on_small_or_enlarged_screens(ui):
    from playwright.sync_api import expect

    page, _ = _open(ui, size=(1440, 1000))
    for size, expected in [
        ((1440, 1000), "sticky"),
        ((390, 844), "static"),
        ((844, 390), "static"),
    ]:
        page.set_viewport_size({"width": size[0], "height": size[1]})
        nav = page.locator(".report-jump-links")
        assert nav.evaluate("element => getComputedStyle(element).position") == expected
        page.get_by_role("link", name="Devices", exact=True).click()
        page.wait_for_function("""() => {
            const nav = document.querySelector('.report-jump-links');
            const target = document.querySelector('#devices-title').getBoundingClientRect();
            return target.top >= 0 && (getComputedStyle(nav).position !== 'sticky'
                || target.top >= nav.getBoundingClientRect().bottom); }""")
        expect(page.locator("#devices-title")).to_be_in_viewport()
    page.set_viewport_size({"width": 768, "height": 1024})
    page.add_style_tag(content="html {font-size: 200% !important}")
    page.wait_for_function("""() => {
        const nav = document.querySelector('.report-jump-links');
        return nav.getBoundingClientRect().height <= 160
            || getComputedStyle(nav).position === 'static'; }""")
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")


def test_followup_practical_setting_and_page_help_is_visible_beside_actions(ui):
    from playwright.sync_api import expect

    page, report = _open(ui)
    for port, expected in [(80, "Do not"), (135, "Windows Security")]:
        service = next(item for item in report.services if item.port == port)
        finding = next(item for item in report.findings if item.service_id == service.service_id)
        page.locator(f'#findingsList [data-finding-id="{finding.finding_id}"]').click()
        practical = page.locator("#detailPanel .practical-help")
        expect(practical).to_be_visible()
        expect(practical).to_contain_text("Where to look and what to check")
        expect(practical).to_contain_text(expected)
        expect(page.locator("#detailPanel > details").last).not_to_have_attribute("open", "")


def test_followup_scan_choices_lead_with_purpose_and_keep_exact_coverage_accessible(ui):
    from playwright.sync_api import expect

    page, base, _ = ui
    page.goto(base + "/")
    expect(page.locator("#scanLaunchButton")).to_be_enabled()
    expect(page.get_by_role("button", name="Light", exact=False)).to_contain_text(
        "across your network"
    )
    expect(page.get_by_role("button", name="Deep", exact=False)).to_contain_text("one device")
    page.get_by_text("What does each scan check?", exact=True).click()
    coverage = page.get_by_text("What does each scan check?", exact=True).locator("..")
    expect(coverage).to_contain_text("12")
    expect(coverage).to_contain_text("65,535")
    expect(page.locator("#scanProgress")).not_to_have_attribute("aria-live", "polite")
    expect(page.locator("#scan-progress-status")).to_have_attribute("aria-live", "polite")
    page.goto(base + "/deep")
    expect(page.get_by_label("Device address (IP) for the Deep scan", exact=True)).to_be_visible()


def test_home_setup_has_one_primary_action_after_choices_and_permission(ui):
    """The primary action belongs to its setup, with no duplicate page launchers."""
    from playwright.sync_api import expect

    page, base, _ = ui
    for width, height in VIEWPORTS:
        page.set_viewport_size({"width": width, "height": height})
        page.goto(base + "/")
        expect(page.locator("#scanLaunchButton")).to_be_enabled()
        expect(page.get_by_role("navigation", name="Independent scan pages")).to_have_count(0)
        expect(
            page.locator('.scan-landing a[href="/light"], .scan-landing a[href="/deep"]')
        ).to_have_count(0)
        expect(page.get_by_role("group", name="Choose a scan")).to_be_visible()
        expect(page.locator(".scan-setup-card .scan-launch")).to_have_count(1)
        expect(page.locator(".scan-extra-details")).not_to_have_attribute("open", "")
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
        action = page.locator("#scanLaunchButton").bounding_box()
        modes = page.locator(".scan-mode").bounding_box()
        notice = page.locator("#scan-notice").bounding_box()
        readiness = page.locator("#scan-config").bounding_box()
        assert action["y"] >= notice["y"] + notice["height"] + 8
        assert notice["y"] >= readiness["y"] + readiness["height"] + 8
        assert action["y"] > modes["y"] + modes["height"]
        assert abs(action["x"] - modes["x"]) <= 1
        assert abs(action["width"] - modes["width"]) <= 1
        assert action["height"] >= 44
        # Choosing a mode never submits a scan; the fixture rejects every scan POST.
        page.get_by_role("button", name="Deep", exact=False).click()
        expect(
            page.get_by_label("Device address (IP) for the Deep scan", exact=True)
        ).to_be_visible()
        page.wait_for_function("document.querySelector('#recentDeviceNote').textContent.length > 0")
        expect(page.locator(".scan-start-area #scanLaunchButton")).to_be_enabled()
        page.get_by_role("button", name="Light", exact=False).click()
        expect(page.locator(".scan-target-fields")).not_to_be_visible()
        page.screenshot(
            path=str(Path(os.environ["APP_DATA_DIR"]).parent / f"home-{width}.png"),
            full_page=True,
        )


def test_home_setup_reflows_with_enlarged_text_and_keeps_native_keyboard_choices(ui):
    from playwright.sync_api import expect

    page, base, _ = ui
    page.set_viewport_size({"width": 768, "height": 1024})
    page.goto(base + "/")
    expect(page.locator("#scanLaunchButton")).to_be_enabled()
    page.add_style_tag(content="html { font-size: 200% !important; }")
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    light = page.get_by_role("button", name="Light", exact=False)
    deep = page.get_by_role("button", name="Deep", exact=False)
    light.focus()
    page.keyboard.press("Tab")
    expect(deep).to_be_focused()
    page.keyboard.press("Enter")
    expect(deep).to_have_attribute("aria-pressed", "true")
    expect(page.locator("#deepHostInput")).to_be_visible()
    page.wait_for_function("document.querySelector('#recentDeviceNote').textContent.length > 0")
    expect(deep).to_be_focused()
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    for control in page.locator(
        ".scan-setup-card button, .scan-setup-card input, .scan-setup-card select"
    ).all():
        if control.is_visible():
            box = control.bounding_box()
            assert box["x"] >= 0 and box["x"] + box["width"] <= 769
            assert box["height"] >= 44
    page.screenshot(
        path=str(Path(os.environ["APP_DATA_DIR"]).parent / "home-enlarged.png"), full_page=True
    )
