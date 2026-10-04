"""User-requested CVE references with synthetic NVD/Ollama; no device traffic."""

import os
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn
from app.main import create_app
from app.scanner.cve import NvdClient
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.json_store import JsonStore
from tests.fixtures.fixtures import make_telnet_scan
from tests.fixtures.provider import ReviewedProvider

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in browser checks"),
]


@pytest.mark.parametrize("version_known", [True, False])
def test_cve_lookup_links_and_saved_references_on_mobile(monkeypatch, tmp_path, version_known):
    from playwright.sync_api import expect, sync_playwright

    fixture = make_telnet_scan()
    fixture["service"].update(
        cpes=["cpe:/a:example:telnet:1.0" if version_known else "cpe:/a:example:telnet"]
    )
    doc = ScanDocument(
        scan_id=fixture["device"]["scan_id"],
        phase="finished",
        state="completed",
        target={"mode": "known_hosts", "hosts": [fixture["device"]["ip"]]},
        devices=[fixture["device"]],
        services=[fixture["service"]],
        findings=[fixture["finding"]],
    )
    store = JsonStore(Path(os.environ["APP_DATA_DIR"]))
    store._create_scan(doc)
    calls = []

    def nvd(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "totalResults": 1,
                "vulnerabilities": [
                    {
                        "cve": {
                            "id": "CVE-2026-10001",
                            "vulnStatus": "Analyzed",
                            "descriptions": [
                                {
                                    "lang": "en",
                                    "value": "Synthetic <script>untrusted</script> text.",
                                }
                            ],
                        }
                    }
                ],
            },
        )

    manager = SessionManager()
    app = create_app(session_manager=manager)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    monkeypatch.setenv("APP_PORT", str(port))
    server = uvicorn.Server(uvicorn.Config(app, log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started
        app.state.nvd = NvdClient(httpx.MockTransport(nvd))
        app.state.explanations.provider = ReviewedProvider()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 390, "height": 844})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            url = manager.get_bootstrap_url(port).replace("/#", f"/scans/{doc.scan_id}#")
            page.goto(url)
            panel = page.locator("#detailPanel .cve-references")
            expect(panel).to_be_visible()
            if not version_known:
                expect(panel.get_by_role("button")).to_have_count(0)
                expect(panel).to_contain_text("did not identify a precise software fingerprint")
                assert not calls and not errors
                browser.close()
                return
            button = panel.get_by_role("button", name="Check CVEs for this software")
            expect(button).to_be_visible()
            assert not calls
            button.click()
            link = panel.get_by_role("link", name="CVE-2026-10001", exact=True)
            expect(link).to_have_attribute(
                "href", "https://nvd.nist.gov/vuln/detail/CVE-2026-10001"
            )
            expect(panel).to_contain_text("possible matches, not confirmed vulnerabilities")
            expect(panel).to_contain_text("Local Ollama selected")
            assert panel.locator("script").count() == 0
            page.reload()
            expect(link).to_be_visible()
            assert len(calls) == 1
            panel.get_by_role("button", name="Check CVEs again").click()
            expect(panel.get_by_role("button", name="Check CVEs again")).to_be_enabled()
            assert len(calls) == 1
            assert not errors
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            page.screenshot(path=str(tmp_path / "cve-mobile.png"), full_page=True)
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        listener.close()
