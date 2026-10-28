"""Lost HTTP reply and refresh against a real backend; all scan/AI work synthetic."""

import asyncio
import os
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from app.main import create_app
from app.scanner.runner import ProcessResult
from app.security.session import SessionManager
from tests.fixtures.browser import browser_listener, wait_for_report_ready
from tests.fixtures.provider import ReviewedProvider

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browsers"),
]


def test_lost_start_reply_refresh_recovers_one_original_scan(monkeypatch, browser_engine):
    from playwright.sync_api import expect, sync_playwright

    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    for module in ("app.api.session", "app.api.scans"):
        monkeypatch.setattr(f"{module}.detect_private_network", lambda: "192.168.56.0/24")
        monkeypatch.setattr(f"{module}.nmap_preflight", lambda _: (True, "synthetic"))
    monkeypatch.setattr("app.api.session.nmap_interface_choices", lambda _: [])
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda _: "synthetic-nmap")
    monkeypatch.setattr("app.api.scans.mdns_available", lambda: False)
    release = threading.Event()
    entered = threading.Event()
    xml = (Path(__file__).parent / "fixtures" / "nmap_host.xml").read_bytes()

    async def runner(args, timeout_s, cancel):
        entered.set()
        while not release.is_set() and not cancel.is_set():
            await asyncio.sleep(0.01)
        return ProcessResult(xml, b"", 0, 0.01, cancelled=cancel.is_set())

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
        app.state.explanations.provider = ReviewedProvider()
        app.state.supervisor.process_runner = runner
        base = f"http://127.0.0.1:{port}"
        with sync_playwright() as playwright:
            browser = getattr(playwright, browser_engine).launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844})
            errors, posts = [], []
            page.on("pageerror", lambda error: errors.append(str(error)))
            recovering = True
            native_status = app.state.start_requests.status

            def lose_reply(route):
                posts.append(route.request.post_data_json)
                response = route.fetch()
                assert response.status == 202
                route.abort("failed")  # The backend accepted it; only its HTTP reply is lost.

            async def status_reply(operation):
                # Control the synthetic server's read view, not a browser
                # route.fetch/fulfill response that can race an unloaded frame.
                response = await native_status(operation)
                if recovering:
                    return {"state": "preparing"}
                return response

            page.route("**/api/live-scans", lose_reply)
            monkeypatch.setattr(app.state.start_requests, "status", status_reply)
            page.goto(manager.get_bootstrap_url(port))
            expect(page.locator("#scanLaunchButton")).to_be_enabled()
            page.goto(base + "/light#setup=1&profile=light&hosts=192.168.56.10")
            expect(page.locator("#scanLaunchButton")).to_be_enabled()
            page.locator("#scanLaunchButton").click()
            expect(page.locator("#scanStartRecover")).to_be_visible()
            expect(page.locator("#scanLaunchButton")).to_be_disabled()
            assert len(posts) == 1 and entered.wait(3)
            operation = posts[0]["operation_id"]
            assert page.url.endswith(f"#start={operation}")
            # Finish the preparing-state receipt read before reloading.
            # The backend scan remains running; held-read navigation is covered
            # separately with both progress and receipt requests.
            expect(page.locator("#scanStartRecover")).to_be_enabled()
            page.reload()
            expect(page.locator("#scanStartRecover")).to_be_visible()
            expect(page.locator("#scanLaunchButton")).to_be_disabled()
            expect(page.locator("#scanStartRecover")).to_be_enabled()
            assert len(posts) == 1
            recovering = False
            # Bounded read-only polling can win the race with a manual click.
            # Both recover the same receipt; neither may send a second POST.
            page.wait_for_url("**#scan=*")
            scan_id = page.url.split("#scan=")[1]
            assert str(app.state.start_requests._transaction(operation).scan_id) == scan_id
            assert len(list(app.state.store.data_root.glob("scans/*/scan.json"))) == 1
            release.set()
            page.wait_for_url(f"**/scans/{scan_id}", timeout=30000)
            wait_for_report_ready(page)
            assert len(posts) == 1 and not errors
            browser.close()
    finally:
        release.set()
        server.should_exit = True
        thread.join(timeout=15)
        listener.close()
        assert not thread.is_alive()
