"""User-requested CVE references with synthetic NVD/Ollama; no device traffic."""

import os
import threading
import time
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
import uvicorn
from app.main import create_app
from app.scanner.cve import NvdClient
from app.schemas.cve import CveLookup
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.annotations import AnnotationStore
from app.storage.json_store import JsonStore
from tests.fixtures.browser import browser_listener, wait_for_report_ready
from tests.fixtures.fixtures import make_telnet_scan
from tests.fixtures.provider import ReviewedProvider

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in browser checks"),
]
RELATED_CRITERIA = "cpe:2.3:a:example:telnet:0.9:*:*:*:*:*:*:*"


@pytest.mark.parametrize("version_known", [True, False])
@pytest.mark.parametrize("lost_response", [False, True])
def test_cve_lookup_links_and_saved_references_on_mobile(
    monkeypatch, tmp_path, version_known, lost_response, browser_engine
):
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
    earlier = None
    if lost_response:
        earlier = (
            AnnotationStore(store)
            ._update(
                doc.scan_id,
                cve=CveLookup(
                    service_id=fixture["service"]["service_id"],
                    checked_at="2026-10-16T12:00:00Z",
                    status="no_matches",
                    message="Earlier saved lookup; not the current attempt.",
                ),
            )
            .model_dump(mode="json")
        )
    calls = []

    def nvd(request):
        calls.append(request)
        related = "virtualMatchString" in request.url.params
        return httpx.Response(
            200,
            json={
                "totalResults": 1,
                "vulnerabilities": [
                    {
                        "cve": {
                            "id": "CVE-2026-10002" if related else "CVE-2026-10001",
                            "vulnStatus": "Analyzed",
                            "descriptions": [
                                {
                                    "lang": "en",
                                    "value": "Synthetic <script>untrusted</script> text.",
                                }
                            ],
                            "references": [
                                {
                                    "url": "https://vendor.example/security/advice",
                                    "tags": ["Vendor Advisory"],
                                },
                                {"url": "http://127.0.0.1/private", "tags": ["Vendor Advisory"]},
                            ],
                            "configurations": [
                                {
                                    "nodes": [
                                        {
                                            "cpeMatch": [
                                                {
                                                    "vulnerable": True,
                                                    "criteria": RELATED_CRITERIA,
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ],
                        }
                    }
                ],
            },
        )

    manager = SessionManager()
    app = create_app(session_manager=manager)
    listener = browser_listener()
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
        app.state.nvd.request_interval_s = 0
        app.state.explanations.provider = ReviewedProvider()
        with sync_playwright() as playwright:
            browser = getattr(playwright, browser_engine).launch()
            page = browser.new_page(viewport={"width": 390, "height": 844})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            url = manager.get_bootstrap_url(port).replace("/#", f"/scans/{doc.scan_id}#")
            page.goto(url)
            panel = page.locator("#detailPanel .cve-references")
            expect(panel).to_be_visible()
            button = panel.locator('[data-device-action="cve-lookup"]')
            panel.locator("details > summary").first.click()
            expect(button).to_be_visible()
            expect(button).to_be_enabled()
            assert not calls
            submissions = []
            page.on(
                "request",
                lambda request: (
                    submissions.append(request.url)
                    if request.method == "POST" and request.url.endswith("/cves")
                    else None
                ),
            )
            if lost_response:

                def lose_saved_response(route):
                    # The real synthetic backend saves successfully; only its
                    # response is lost. Another tab's explicit cached request
                    # replaces the latest receipt before the first tab recovers.
                    first = route.fetch()
                    assert first.status == 200
                    operation = first.json()["lookup"]["operation_id"]
                    second = route.fetch(post_data={"operation_id": str(uuid4())})
                    assert second.status == 200
                    later = second.json()["lookup"]
                    assert later["operation_id"] != operation
                    assert operation in {
                        item["operation_id"] for item in later["operation_receipts"]
                    }
                    # GET recovery must recognise the earlier retained receipt;
                    # it must not repeat this tab's original POST automatically.
                    route.abort()

                page.route("**/services/*/cves", lose_saved_response)
            button.click()
            if lost_response:
                expect(panel.locator(".cve-status")).to_contain_text("may still finish and save")
                retry = panel.get_by_role("button", name="Check CVEs again", exact=True)
                expect(retry).to_be_disabled()
                page.unroute("**/services/*/cves")
                reload_saved = panel.get_by_role("button", name="Reload saved CVE references")
                # A newer annotation revision due to an unrelated edit must not
                # make the old lookup confirm the lost request.
                page.route(
                    "**/annotations",
                    lambda route: route.fulfill(
                        json={
                            **earlier,
                            "revision": earlier["revision"] + 1,
                            "title": "Unrelated saved title",
                        }
                    ),
                )
                reload_saved.click()
                expect(retry).to_be_disabled()
                expect(panel.locator(".cve-status")).to_contain_text("still unconfirmed")
                expect(panel).to_contain_text("Earlier saved lookup")
                page.unroute("**/annotations")
                reload_saved.click()
                expect(reload_saved).not_to_be_visible()
                expect(retry).to_be_enabled()
                expect(retry).to_be_focused()
            assert len(submissions) == 1
            cve_id = "CVE-2026-10001" if version_known else "CVE-2026-10002"
            link = panel.get_by_role("link", name=cve_id, exact=True)
            expect(link).to_have_attribute("href", "https://nvd.nist.gov/vuln/detail/" + cve_id)
            advice = panel.get_by_role(
                "link", name="Maker's advice — vendor.example (NVD reference)"
            )
            expect(advice.first).to_have_attribute("href", "https://vendor.example/security/advice")
            assert panel.locator('a[href*="/private"]').count() == 0
            expect(panel).to_contain_text("Related software problems — version not verified")
            expect(panel).to_contain_text("not matches confirmed for your device")
            if version_known:
                expect(panel).to_contain_text("Local Ollama selected")
                expect(panel.get_by_role("link", name="CVE-2026-10002", exact=True)).to_be_visible()
            else:
                expect(panel).to_contain_text("Version not identified")
                expect(panel.get_by_role("link", name="CVE-2026-10001", exact=True)).to_have_count(
                    0
                )
            assert panel.locator("script").count() == 0
            page.reload()
            # Reading state preserves this open disclosure across refresh.
            wait_for_report_ready(page)
            expect(panel.locator("details").first).to_have_attribute("open", "")
            expect(link).to_be_visible()
            assert len(calls) == (2 if version_known else 1)
            if lost_response:
                # Cached research retains its old checked_at and references,
                # but still saves a distinct receipt for this second attempt.
                page.route("**/services/*/cves", lose_saved_response)
            panel.get_by_role("button", name="Check CVEs again").click()
            if lost_response:
                expect(panel.get_by_role("button", name="Check CVEs again")).to_be_disabled()
                page.unroute("**/services/*/cves")
                panel.get_by_role("button", name="Reload saved CVE references").click()
            expect(panel.get_by_role("button", name="Check CVEs again")).to_be_enabled()
            assert len(submissions) == 2
            assert len(calls) == (2 if version_known else 1)
            assert not errors
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            page.screenshot(path=str(tmp_path / "cve-mobile.png"), full_page=True)
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        listener.close()
