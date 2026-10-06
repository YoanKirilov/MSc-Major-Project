"""Synthetic end-to-end library tools; no device traffic or live model calls."""

import os
import socket
import threading
import time
from pathlib import Path
from uuid import uuid4

import pytest
import uvicorn
from app.main import create_app
from app.schemas.common import iso_z, utc_now
from app.schemas.cve import CveLookup
from app.schemas.scan import Device, DeviceDetail, ScanDocument
from app.security.session import SessionManager
from app.storage.annotations import NameRefresh
from app.storage.json_store import JsonStore
from tests.fixtures.fixtures import make_telnet_scan

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browser"),
]


def test_search_picker_titles_nickname_sync_and_identification(monkeypatch, tmp_path):
    from playwright.sync_api import expect, sync_playwright

    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.0.0/24")
    monkeypatch.setattr("app.api.session.detect_private_network", lambda: "192.168.0.0/24")
    monkeypatch.setattr("app.api.library.detect_private_network", lambda: "192.168.0.0/24")
    monkeypatch.setattr("app.api.session.nmap_preflight", lambda config: (True, "synthetic"))
    monkeypatch.setattr("app.api.session.nmap_interface_choices", lambda config: [])

    async def unavailable(self):
        return False

    lookup_count = 0

    async def lookup(device, scope, interface):
        nonlocal lookup_count
        lookup_count += 1
        return NameRefresh(
            device_id=device.device_id,
            checked_at=iso_z(utc_now()),
            names=[]
            if lookup_count > 1
            else [
                {
                    "name": "Later reported name",
                    "source": "reverse_dns",
                    "observed_at": iso_z(utc_now()),
                }
            ],
            notes=["Unverified later name claim."],
        )

    monkeypatch.setattr(
        "app.explanations.service.ExplanationService.provider_available", unavailable
    )
    monkeypatch.setattr("app.api.library.lookup_names", lookup)
    fixture = make_telnet_scan()
    fixture["service"].update(
        detection_method="probed", nmap_confidence=9, cpes=["cpe:/a:example:telnetd:1.0"]
    )

    async def fake_cves(self, service):
        return CveLookup(
            service_id=service.service_id,
            checked_at=iso_z(utc_now()),
            status="no_matches",
            message="Synthetic reference lookup; no network request.",
        )

    async def fake_explanation(record, provider, **kwargs):
        return record

    monkeypatch.setattr("app.scanner.cve.NvdClient.lookup", fake_cves)
    monkeypatch.setattr("app.api.cves.explain_cves", fake_explanation)
    scan_id = fixture["device"]["scan_id"]
    store = JsonStore(Path(os.environ["APP_DATA_DIR"]))
    doc = ScanDocument(
        scan_id=scan_id,
        state="completed",
        phase="finished",
        target={"mode": "known_hosts", "hosts": ["192.168.0.10", "192.168.0.11"]},
        policy={"profile": "light", "allowed_network": "192.168.0.0/24"},
        devices=[
            Device.model_validate(fixture["device"]),
            Device(
                device_id=str(uuid4()),
                scan_id=scan_id,
                ip="192.168.0.11",
                hostname="Bedroom display",
            ),
        ],
        services=[fixture["service"]],
        findings=[fixture["finding"]],
    )
    for device in doc.devices:
        device.details.append(
            DeviceDetail(
                kind="history",
                label="Earlier observations",
                value="No verified identity match.",
                source="saved reports",
                status="inferred",
            )
        )
    store._create_scan(doc)
    primary = store._scan_dir(scan_id) / "scan.json"
    evidence = primary.read_bytes()
    manager = SessionManager()
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    monkeypatch.setenv("APP_PORT", str(port))
    server = uvicorn.Server(uvicorn.Config(create_app(session_manager=manager), log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started
        base = f"http://127.0.0.1:{port}"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            errors, scans = [], []
            context.on("page", lambda page: page.on("pageerror", lambda e: errors.append(str(e))))
            context.on(
                "request",
                lambda req: (
                    scans.append(req.url)
                    if req.method == "POST" and req.url.endswith("/api/live-scans")
                    else None
                ),
            )
            page = context.new_page()
            page.goto(manager.get_bootstrap_url(port))
            expect(page.locator("#scanLaunchButton")).to_be_enabled()
            page.goto(base + f"/scans/{scan_id}")
            expect(
                page.locator("#device-summaries .device-summary-group > .device-summary")
            ).to_have_count(2)
            for group in page.locator("#device-summaries .device-summary-group").all():
                card_bounds = group.locator(".device-summary").bounding_box()
                tools_bounds = group.locator(".device-name-tools").bounding_box()
                assert tools_bounds["y"] >= card_bounds["y"] + card_bounds["height"]
                assert (
                    card_bounds["x"] <= tools_bounds["x"] < card_bounds["x"] + card_bounds["width"]
                )
            expect(page.get_by_role("searchbox", name="Search devices and results")).to_be_visible()
            expect(page.locator("#comparison-summary")).to_contain_text("could not be compared")
            page.get_by_text("View comparison details", exact=True).click()
            expect(page.locator("#comparison-list article").first).to_contain_text("192.168.0.10")
            expect(page.locator("#comparison-list article").nth(1)).to_contain_text("192.168.0.11")
            page.locator("#searchInput").fill("display bedroom")
            expect(
                page.locator("#device-summaries .device-summary-group > .device-summary")
            ).to_have_count(1)
            expect(page.locator("#device-search-count")).to_contain_text("1 of 2")
            expect(page.locator("#findingsList")).to_contain_text("No review items match")
            page.locator("#clearSearchButton").click()
            expect(
                page.locator("#device-summaries .device-summary-group > .device-summary")
            ).to_have_count(2)

            other = context.new_page()
            other.goto(base + f"/scans/{scan_id}")
            expect(other.locator("#findingsList .finding-card")).to_have_count(1)
            first_status = page.locator("#detailPanel .action-check select").first
            first_status.focus()
            first_status.select_option("checked")
            expect(first_status).to_have_value("checked")
            expect(page.locator("#checklist-notice")).to_contain_text("Checklist saved")
            expect(first_status).to_be_focused()
            expect(page.locator("#detailPanel .action-check").first).to_contain_text(
                "Checklist saved"
            )
            expect(page.locator("#nextStepsList .action-check select").first).to_have_value(
                "checked"
            )
            stale_status = other.locator("#detailPanel .action-check select").first
            stale_status.select_option("need_help")
            expect(other.locator("#checklist-notice")).to_contain_text("not saved")
            expect(other.locator("#detailPanel .action-check").first).to_contain_text("not saved")
            expect(stale_status).to_have_value("checked")
            stale_status.select_option("need_help")
            expect(stale_status).to_have_value("need_help")
            expect(other.locator("#checklist-notice")).to_contain_text("Checklist saved")
            page.reload()
            expect(page.locator("#detailPanel .action-check select").first).to_have_value(
                "need_help"
            )
            page.set_viewport_size({"width": 390, "height": 844})
            page.reload()
            expect(
                page.locator("#device-summaries .device-summary-group > details[open]")
            ).to_have_count(0)
            expect(page.locator(".device-name-tools button").first).to_be_visible()
            page.locator("#identifyFirstDevice").click()
            expect(page.locator("#searchInput")).to_have_value("192.168.0.10")
            expect(
                page.locator("#device-summaries .device-summary-group > details").first
            ).to_have_attribute("open", "")
            expect(page.locator(".device-name-tools button").first).to_be_focused()
            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
            page.set_viewport_size({"width": 1280, "height": 900})
            page.locator("#clearSearchButton").click()
            other.locator("#searchInput").fill("192.168.0.10")
            page.once("dialog", lambda dialog: dialog.accept("Kitchen TV"))
            page.get_by_role("button", name="Add your own nickname", exact=True).first.click()
            expect(page.locator("#device-summaries")).to_contain_text("Kitchen TV")
            other.bring_to_front()
            expect(other.locator("#device-summaries")).to_contain_text("Kitchen TV", timeout=15000)
            expect(other.locator("#searchInput")).to_have_value("192.168.0.10")
            expect(other.locator("#findingsList .finding-card")).to_have_count(1)
            page.locator("#searchInput").fill("TV kitchen")
            expect(
                page.locator("#device-summaries .device-summary-group > .device-summary")
            ).to_have_count(1)
            page.once("dialog", lambda dialog: dialog.accept("After router update"))
            page.locator("#editReportTitle").click()
            expect(page.locator("#report-user-title")).to_have_text("After router update")
            page.once("dialog", lambda dialog: dialog.accept())
            page.get_by_role("button", name="Try identifying this address again").click()
            expect(page.locator("#device-summaries")).to_contain_text("Later reported name")
            expect(page.locator(".identification-status")).to_contain_text("1 reported name")
            page.once("dialog", lambda dialog: dialog.accept())
            page.get_by_role("button", name="Try identifying this address again").click()
            expect(page.locator(".identification-status")).to_contain_text("No new name found")
            expect(page.locator(".identification-status")).to_be_visible()
            # A second tab edits the checklist. Name and CVE responses carry full
            # newer snapshots; adopting them must synchronise every control.
            other.reload()
            second_status = other.locator("#detailPanel .action-check select").first
            expect(second_status).to_have_value("need_help")
            second_status.select_option("checked")
            expect(other.locator("#checklist-notice")).to_contain_text("Checklist saved")
            page.locator('[data-filter="high"]').click()
            refresh_button = page.get_by_role("button", name="Try identifying this address again")
            refresh_button.focus()
            page.once("dialog", lambda dialog: dialog.accept())
            refresh_button.click()
            expect(page.locator("#detailPanel .action-check select").first).to_have_value("checked")
            expect(page.locator("#nextStepsList .action-check select").first).to_have_value(
                "checked"
            )
            expect(refresh_button).to_be_focused()
            expect(page.locator("#searchInput")).to_have_value("TV kitchen")
            expect(page.locator("#checklist-progress")).to_contain_text("1 of 2")
            expect(page.locator('[data-filter="high"]')).to_have_attribute("aria-pressed", "true")
            second_status.select_option("need_help")
            expect(other.locator("#checklist-notice")).to_contain_text("not saved")
            second_status.select_option("need_help")
            expect(other.locator("#checklist-notice")).to_contain_text("Checklist saved")
            other.once("dialog", lambda dialog: dialog.accept("Title from second tab"))
            other.locator("#editReportTitle").click()
            expect(other.locator("#report-user-title")).to_have_text("Title from second tab")
            cve = page.locator("#detailPanel .cve-references button")
            cve.focus()
            cve.click()
            expect(page.locator("#report-user-title")).to_have_text("Title from second tab")
            expect(page.locator("#detailPanel .action-check select").first).to_have_value(
                "need_help"
            )
            expect(page.locator("#nextStepsList .action-check select").first).to_have_value(
                "need_help"
            )
            expect(cve).to_be_focused()
            expect(page.locator("#searchInput")).to_have_value("TV kitchen")
            saved_notes = context.request.get(
                base + f"/api/live-scans/{scan_id}/annotations"
            ).json()
            stale_notes = {
                **saved_notes,
                "revision": saved_notes["revision"] - 1,
                "title": "Stale title",
                "action_checks": [],
            }
            page.route(
                "**/services/*/cves",
                lambda route: route.fulfill(
                    json={"annotations": stale_notes, "lookup": saved_notes["cve_lookups"][0]}
                ),
            )
            cve.click()
            expect(cve).to_have_text("Check CVEs again")
            expect(page.locator("#report-user-title")).to_have_text("Title from second tab")
            expect(page.locator("#detailPanel .action-check select").first).to_have_value(
                "need_help"
            )
            page.unroute("**/services/*/cves")
            page.locator("#checklist-filter").select_option("checked")
            expect(page.locator("#nextStepsList .action-check").first).to_be_hidden()
            page.locator("#checklist-filter").select_option("need_help")
            expect(page.locator("#nextStepsList .action-check").first).to_be_visible()
            page.locator("#checklist-filter").select_option("all")
            # Restore the title used by the later search checks with the current revision.
            page.once("dialog", lambda dialog: dialog.accept("After router update"))
            page.locator("#editReportTitle").click()
            expect(page.locator("#report-user-title")).to_have_text("After router update")
            page.route("**/refresh-name", lambda route: route.fulfill(status=503, body="{}"))
            page.once("dialog", lambda dialog: dialog.accept())
            page.get_by_role("button", name="Try identifying this address again").click()
            expect(page.locator(".identification-status")).to_contain_text(
                "Name lookup could not finish"
            )
            expect(
                page.get_by_role("button", name="Try identifying this address again")
            ).to_be_enabled()

            picker = context.new_page()
            picker.goto(base + "/deep")
            expect(picker.locator("#recentDeviceSelect")).to_contain_text("Kitchen TV")
            expect(picker.locator("#recentDeviceSelect")).to_contain_text("response not confirmed")
            for width in (320, 390):
                picker.set_viewport_size({"width": width, "height": 844})
                assert not picker.evaluate("document.documentElement.scrollWidth > innerWidth")
                picker.screenshot(path=str(tmp_path / f"picker-context-{width}.png"))
            picker.set_viewport_size({"width": 1280, "height": 900})
            picker.locator("#recentDeviceSelect").select_option("192.168.0.10")
            expect(picker.locator("#deepHostInput")).to_have_value("192.168.0.10")
            with picker.expect_response("**/api/recent-devices"):
                picker.locator("#refreshDeviceChoices").click()
            expect(picker.locator("#recentDeviceSelect")).to_have_value("192.168.0.10")
            picker.route(
                "**/api/recent-devices",
                lambda route: route.fulfill(json={"items": [], "total": 0, "days": 7}),
            )
            with picker.expect_response("**/api/recent-devices"):
                picker.locator("#refreshDeviceChoices").click()
            expect(picker.locator("#recentDeviceSelect")).to_have_value("")
            expect(picker.locator("#deepHostInput")).to_have_value("192.168.0.10")
            expect(picker.locator("#recentDeviceNote")).to_contain_text("It has been kept")
            picker.unroute("**/api/recent-devices")
            picker.locator("#deepHostInput").fill("192.168.0.99")
            expect(picker.locator("#recentDeviceSelect")).to_have_value("")
            with picker.expect_response("**/api/recent-devices"):
                picker.locator("#refreshDeviceChoices").click()
            expect(picker.locator("#deepHostInput")).to_have_value("192.168.0.99")
            expect(picker.locator("#recentDeviceNote")).to_contain_text("It has been kept")
            expect(picker.locator("#recentDeviceNote")).to_contain_text(
                "Addresses may have changed"
            )
            page.goto(base + "/history")
            page.locator("#history-query").fill("update router")
            page.get_by_role("button", name="Search reports", exact=True).click()
            expect(page.locator("#history-list")).to_contain_text("After router update")
            page.locator("#history-profile").select_option("deep-tcp-v1")
            page.get_by_role("button", name="Search reports", exact=True).click()
            expect(page.locator("#history-status")).to_contain_text("No reports match your filters")
            broken = ScanDocument(
                scan_id=str(uuid4()), target={"mode": "known_hosts", "hosts": ["192.168.0.99"]}
            )
            store._create_scan(broken)
            store._atomic_write(store._scan_dir(broken.scan_id) / "scan.json", "broken fixture")
            page.get_by_role("button", name="Search reports", exact=True).click()
            expect(page.locator("#history-warnings")).to_contain_text("1 saved report(s)")
            expect(page.locator("#history-list li")).to_have_count(0)
            page.route("**/annotations", lambda route: route.fulfill(status=503, body="{}"))
            page.goto(base + f"/scans/{scan_id}")
            expect(
                page.locator("#device-summaries .device-summary-group > .device-summary")
            ).to_have_count(2)
            expect(page.locator("#annotation-notice")).to_contain_text(
                "The original scan results are still shown"
            )
            expect(page.locator("#editReportTitle")).to_be_disabled()
            expect(page.locator("#detailPanel .action-check select").first).to_be_disabled()
            page.goto(base + "/settings")
            expect(page.locator("#scope-mode")).to_have_value("automatic")
            expect(page.locator("#allowed-network")).to_be_disabled()
            expect(page.locator("#network-status")).to_contain_text("backend configuration")
            page.locator("#scope-mode").select_option("manual")
            page.locator("#allowed-network").fill("192.168.0.0/24")
            page.get_by_role("button", name="Save settings", exact=True).click()
            page.wait_for_url(base + "/")
            page.goto(base + "/settings")
            expect(page.locator("#scope-mode")).to_have_value("manual")
            expect(page.locator("#allowed-network")).to_have_value("192.168.0.0/24")
            page.locator("#scope-mode").select_option("automatic")
            page.get_by_role("button", name="Save settings", exact=True).click()
            page.wait_for_url(base + "/")
            assert store._load_settings().allowed_network is None
            assert not errors and not scans
            browser.close()
        assert primary.read_bytes() == evidence
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        listener.close()
