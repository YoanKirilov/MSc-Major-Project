"""Responsive synthetic reports; no Nmap, Ollama or device requests."""

import os
import socket
import threading
import time
from pathlib import Path
from uuid import uuid4

import pytest
import uvicorn
from app.main import create_app
from app.risk.engine import evaluate_device
from app.scanner.parser import parse_host
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.json_store import JsonStore

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in browser matrix"),
]
SIZES = [
    (320, 568),
    (390, 844),
    (844, 390),
    (768, 1024),
    (1024, 768),
    (1280, 720),
    (1920, 1080),
    (2560, 1440),
]


@pytest.mark.parametrize("engine", os.getenv("RESPONSIVE_BROWSERS", "chromium").split(","))
def test_all_pages_reflow_and_deep_dialog(engine, tmp_path, monkeypatch):
    from playwright.sync_api import expect, sync_playwright

    async def unavailable(self):
        return False

    monkeypatch.setattr(
        "app.explanations.service.ExplanationService.provider_available", unavailable
    )
    monkeypatch.setattr("app.api.session.nmap_preflight", lambda config: (True, "synthetic"))
    monkeypatch.setattr("app.api.session.nmap_interface_choices", lambda config: [])
    store = JsonStore(Path(os.environ["APP_DATA_DIR"]))
    scan_id = str(uuid4())
    device, services = parse_host(
        (Path(__file__).parent / "fixtures/nmap_host.xml").read_bytes(), "192.168.56.10", scan_id
    )
    device.hostname = "LongUntrustedDeviceName" * 5
    document = ScanDocument(
        scan_id=scan_id,
        state="completed",
        phase="finished",
        analysis_status="failed",
        target={"mode": "known_hosts", "hosts": [device.ip]},
        policy={"profile": "deep-tcp-v1", "network_context": {"address": device.ip}},
        coverage={
            "candidate_count": 1,
            "service_completed_count": 1,
            "targets": [{"ip": device.ip, "service_status": "completed"}],
        },
        devices=[device],
        services=services,
        findings=evaluate_device(device, services),
    )
    store._create_scan(document)
    partial_id = str(uuid4())
    store._create_scan(
        ScanDocument(
            scan_id=partial_id,
            state="partial",
            phase="finished",
            scan_outcome="partial",
            target={"mode": "known_hosts", "hosts": ["192.168.56.12"]},
            coverage={
                "candidate_count": 1,
                "service_attempted_count": 1,
                "service_failed_count": 1,
                "targets": [
                    {
                        "ip": "192.168.56.12",
                        "service_status": "failed",
                        "attempts": 2,
                        "reason_code": "host_unreachable",
                    }
                ],
            },
            errors=[
                {
                    "code": "HOST_UNREACHABLE",
                    "message": "Device did not respond.",
                    "target_ip": "192.168.56.12",
                }
            ],
        )
    )
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
        with sync_playwright() as playwright:
            browser = getattr(playwright, engine).launch(headless=True)
            context = browser.new_context(reduced_motion="reduce")
            page = context.new_page()
            errors, scan_requests = [], []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on(
                "request",
                lambda req: (
                    scan_requests.append(req.url)
                    if req.method == "POST" and req.url.endswith("/api/live-scans")
                    else None
                ),
            )
            base = f"http://127.0.0.1:{port}"
            page.goto(manager.get_bootstrap_url(port))
            page.wait_for_function("sessionStorage.getItem('network-assessor-csrf') !== null")
            for width, height in SIZES:
                page.set_viewport_size({"width": width, "height": height})
                for route, selector in [
                    ("/", "#scanLaunchButton"),
                    ("/light", "#scanLaunchButton"),
                    ("/deep", "#scanLaunchButton"),
                    ("/settings", "#settings-form"),
                    ("/history", "#history-list"),
                    (f"/scans/{scan_id}", "#first-action"),
                ]:
                    page.goto(base + route)
                    expect(page.locator(selector)).to_be_visible()
                    if route in ("/", "/light", "/deep"):
                        # Render progress without launching a scanner. Whole-page
                        # overflow checks alone miss a percentage wrapping in place.
                        for percentage in ("0%", "90%", "100%", "Running"):
                            for text_scale in ("100%", "200%"):
                                page.evaluate(
                                    """([value, scale]) => {
                                      document.documentElement.style.fontSize = scale;
                                      document.querySelector('#scanProgress').hidden = false;
                                      document.querySelector('#progressPercent').textContent =
                                        value;
                                      document.querySelector('#progressPercent').dataset.activity =
                                        String(value === 'Running');
                                      document.querySelector('#progressDetail').textContent =
                                        'Scanning discovered devices: 0 of 1 complete';
                                    }""",
                                    [percentage, text_scale],
                                )
                                bounds = page.locator("#progressPercent").evaluate(
                                    """element => {
                                      const range = document.createRange();
                                      range.selectNodeContents(element);
                                      return [...range.getClientRects()].map(r => r.top);
                                    }"""
                                )
                                assert len(set(bounds)) == 1, (engine, width, percentage)
                                assert not page.evaluate(
                                    "document.documentElement.scrollWidth > innerWidth"
                                )
                        page.evaluate("document.documentElement.style.fontSize = ''")
                    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth"), (
                        engine,
                        width,
                        height,
                        route,
                    )
                    if route.startswith("/scans/"):
                        expect(page.locator(".next-steps > *")).to_have_count(2)
                        expect(page.locator(".next-steps > div #checklist-filter")).to_have_count(1)
                        expect(page.locator("#self-check-notice")).to_be_visible()
                        expect(page.locator("#device-metric")).to_have_text("1 of 1 selected")
                        expect(page.locator("#report-checks")).to_contain_text("All selected")
                        expect(page.locator("#report-first-step")).to_contain_text(
                            "Computer that ran this scan"
                        )
                        expect(page.locator("#nextStepsList")).to_contain_text(
                            "Computer that ran this scan"
                        )
                        action = page.locator("#first-action").bounding_box()
                        stats = page.locator(".result-summary-card").bounding_box()
                        # Restored layout: guidance belongs below the result summary.
                        assert action["y"] >= stats["y"] + stats["height"]
                        page.locator("#findingsList .finding-card").first.click()
                        expect(page.locator("#detailPanel")).to_contain_text("supporting evidence")
                        page.locator("#runAgainButton").click()
                        expect(page.get_by_role("dialog")).to_be_visible()
                        dialog = page.get_by_role("dialog").bounding_box()
                        assert dialog["x"] >= 0 and dialog["x"] + dialog["width"] <= width + 1
                        page.get_by_role("button", name="Cancel", exact=True).click()
                        expect(page.get_by_role("dialog")).not_to_be_visible()
                    page.screenshot(path=str(tmp_path / f"{engine}-{width}-{selector[1:]}.png"))
            for width in (320, 390):
                page.set_viewport_size({"width": width, "height": 844})
                page.goto(base + f"/scans/{partial_id}")
                expect(page.locator("#scan-problems")).to_be_visible()
                label = page.locator("#scan-problems strong").bounding_box()
                notes = page.locator("#scan-problems ul").bounding_box()
                assert notes["y"] >= label["y"] + label["height"]
                assert label["width"] > 180
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
                page.screenshot(path=str(tmp_path / f"{engine}-{width}-unfinished-checks.png"))
            # 320 CSS pixels approximates reflow at 400% zoom on a 1280px viewport.
            page.set_viewport_size({"width": 320, "height": 568})
            page.goto(base + f"/scans/{scan_id}")
            expect(page.locator("#first-action")).to_be_visible()
            device_card = page.locator("#device-summaries .device-summary-group > details").first
            expect(device_card).not_to_have_attribute("open", "")
            collapsed_height = page.evaluate("document.documentElement.scrollHeight")
            device_card.locator("summary").first.focus()
            page.keyboard.press("Enter")
            expect(device_card).to_have_attribute("open", "")
            assert page.evaluate("document.documentElement.scrollHeight") > collapsed_height
            page.get_by_role("navigation", name="Report sections").get_by_role(
                "link", name="Devices", exact=True
            ).click()
            assert page.url.endswith("#devices-title")
            page.locator("#technical-devices > summary").focus()
            page.keyboard.press("Enter")
            page.locator(".device-table-wrap").focus()
            expect(page.locator(".device-table-wrap")).to_be_focused()
            page.keyboard.press("ArrowRight")
            # Increased text size, separately from narrow-width reflow.
            page.evaluate("document.documentElement.style.fontSize = '200%'")
            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
            assert not errors
            assert not scan_requests
            if engine != "firefox":
                mobile = browser.new_context(
                    viewport={"width": 390, "height": 844},
                    is_mobile=True,
                    has_touch=True,
                    device_scale_factor=2,
                    reduced_motion="reduce",
                )
                touch = mobile.new_page()
                touch.on("pageerror", lambda error: errors.append(str(error)))
                touch.on(
                    "request",
                    lambda req: (
                        scan_requests.append(req.url)
                        if req.method == "POST" and req.url.endswith("/api/live-scans")
                        else None
                    ),
                )
                touch.goto(manager.get_bootstrap_url(port))
                touch.wait_for_function("sessionStorage.getItem('network-assessor-csrf') !== null")
                touch.goto(base + f"/scans/{scan_id}")
                expect(touch.locator("#first-action")).to_be_visible()
                touch.locator("#runAgainButton").tap()
                expect(touch.get_by_role("dialog")).to_be_visible()
                touch.get_by_role("button", name="Same device", exact=True).tap()
                expect(touch.locator("#deepHostInput")).to_have_value(device.ip)
                assert not scan_requests and not errors
                mobile.close()
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        listener.close()
