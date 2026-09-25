"""Real browser, synthetic network/AI. No Nmap process or home-network probes."""

import asyncio
import os
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn
from app.main import create_app
from app.scanner.runner import ProcessResult
from app.schemas.scan import DeviceDetail
from app.security.session import SessionManager
from tests.fixtures.provider import ReviewedProvider

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(
        os.getenv("RUN_BROWSER_TESTS") != "1",
        reason="Set RUN_BROWSER_TESTS=1 for the real browser workflow",
    ),
]


def test_scan_ai_wait_failure_retry_history_and_known_host_rescan(tmp_path, monkeypatch):
    from playwright.sync_api import expect, sync_playwright

    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.8/30")
    monkeypatch.setattr("app.api.session.detect_private_network", lambda: "192.168.56.0/24")
    monkeypatch.setattr("app.api.scans.detect_private_network", lambda: "192.168.56.0/24")
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda config: (True, "test"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda config: "test-nmap")
    monkeypatch.setattr("app.api.session.nmap_preflight", lambda config: (True, "test"))
    monkeypatch.setattr("app.api.session.nmap_interface_choices", lambda config: [])
    released = threading.Event()
    entered = threading.Event()
    fail_ai = threading.Event()
    scanned = []
    xml = (Path(__file__).parent / "fixtures" / "nmap_host.xml").read_bytes()

    class PausedProvider(ReviewedProvider):
        async def generate(self, payload):
            entered.set()
            while not released.is_set():
                await asyncio.sleep(0.01)
            if fail_ai.is_set():
                raise httpx.ConnectError("synthetic provider outage")
            return await super().generate(payload)

    async def runner(args, timeout_s, cancel):
        scanned.append(args[-1])
        return ProcessResult(xml, b"", 0, 0.01)

    async def no_dns(self, ip):
        return None

    async def synthetic_details(device, *args, **kwargs):
        device.details.append(
            DeviceDetail(
                kind="mdns",
                label="Reported model",
                value="Example room display <script>",
                source="mDNS",
                status="advertised",
            )
        )

    monkeypatch.setattr("app.jobs.supervisor.ScanSupervisor._local_hostname", no_dns)
    monkeypatch.setattr("app.scanner.details.network_details", synthetic_details)
    manager = SessionManager()
    app = create_app(session_manager=manager)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    monkeypatch.setenv("APP_PORT", str(port))
    server = uvicorn.Server(uvicorn.Config(app, log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.02)
    assert server.started
    app.state.explanations.provider = PausedProvider()
    app.state.supervisor.process_runner = runner
    base = f"http://127.0.0.1:{port}"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                channel=os.getenv("BROWSER_CHANNEL", "msedge") or None, headless=True
            )
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(manager.get_bootstrap_url(port))
            expect(page.locator("#scan-config")).to_contain_text(
                "Ready to scan your authorised local network"
            )
            page.locator("#scanLaunchButton").click()
            expect(page.locator("#progressPhase")).to_have_text(
                "Making your results easier to understand.", timeout=15000
            )
            assert page.url.rstrip("/") == base
            assert entered.is_set()
            before_refresh = len(scanned)
            page.reload()
            expect(page.locator("#progressPhase")).to_have_text(
                "Making your results easier to understand.", timeout=15000
            )
            expect(page.locator("#scanLaunchButton")).to_be_disabled()
            assert len(scanned) == before_refresh
            released.set()
            page.wait_for_url("**/scans/*", timeout=15000)
            expect(page.locator("#result-title")).to_have_text("Your local scan is ready.")
            expect(page.locator("#resultsSummary")).to_contain_text("Ollama reviewed")
            expect(page.locator("#report-content")).to_be_visible()
            expect(page.locator("#report-first-step")).not_to_be_empty()
            expect(page.locator("#report-checks")).to_contain_text("device")
            extra = (
                page.locator("details")
                .filter(has=page.locator("summary", has_text="More about this device"))
                .last
            )
            extra.locator("summary").first.click()
            expect(extra).to_contain_text("Example room display <script>")
            expect(extra).to_contain_text("Device announcement")
            assert extra.locator("script").count() == 0
            first_report = page.url
            page.get_by_role("link", name="Saved reports").click()
            page.locator("#history-list a").first.click()
            assert page.url == first_report
            # Create a Light known-host result using the actual authenticated API.
            result = page.evaluate("""async () => {
                const response = await fetch('/api/live-scans', {method:'POST',
                  headers:{'Content-Type':'application/json','X-CSRF-Token':sessionStorage.getItem('network-assessor-csrf')},
                  body:JSON.stringify({mode:'known_hosts',hosts:['192.168.56.10'],profile:'light',authorised:true})});
                return response.json();
            }""")
            page.goto(base + "/scans/" + result["scan_id"])
            expect(page.locator("#result-title")).to_have_text(
                "Your local scan is ready.", timeout=15000
            )
            fail_ai.set()
            page.on("dialog", lambda dialog: dialog.accept())
            with page.expect_response(
                lambda response: (
                    response.url.endswith("/api/live-scans") and response.request.method == "POST"
                )
            ) as response:
                page.locator("#runAgainButton").click()
            assert response.value.status == 202
            assert response.value.request.post_data_json["hosts"] == ["192.168.56.10"]
            expect(page.locator("#result-status")).to_contain_text(
                "Simplification unavailable", timeout=15000
            )
            expect(page.locator("#report-content")).to_be_visible()
            count = len(scanned)
            fail_ai.clear()
            page.locator("#simplifyButton").click()
            expect(page.locator("#resultsSummary")).to_contain_text(
                "Ollama reviewed", timeout=15000
            )
            assert len(scanned) == count
            # Both profiles pass through the same detail collector and renderer.
            deep = page.evaluate("""async () => {
                const response = await fetch('/api/live-scans', {method:'POST',
                  headers:{'Content-Type':'application/json','X-CSRF-Token':sessionStorage.getItem('network-assessor-csrf')},
                  body:JSON.stringify({mode:'known_hosts',hosts:['192.168.56.10'],profile:'deep-tcp-v1',authorised:true})});
                if (response.status !== 202) throw new Error('Deep request rejected');
                return response.json();
            }""")
            page.goto(base + "/scans/" + deep["scan_id"])
            expect(page.locator("#result-title")).to_have_text(
                "Your local scan is ready.", timeout=15000
            )
            expect(page.get_by_text("Reported model: Example room display <script>")).to_have_count(
                1
            )
            page.screenshot(path=str(tmp_path / "report.png"), full_page=True)
            page.context.clear_cookies()
            page.goto(base)
            expect(page.locator("#scan-config")).to_contain_text("session has expired")
            page.locator("#scanLaunchButton").click()
            expect(page.locator("#scanError")).to_contain_text("session has expired")
            expect(page.locator("#scanError")).not_to_contain_text("Nmap is not installed")
            assert not errors
            browser.close()
    finally:
        released.set()
        server.should_exit = True
        thread.join(timeout=15)
        listener.close()
