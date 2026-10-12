"""Real report renderer, synthetic delayed responses; no device probes or live AI."""

import json
import os
import re
import threading
import time

import pytest
import uvicorn
from app.main import create_app
from app.security.session import SessionManager
from app.storage.json_store import JsonStore
from tests.fixtures.browser import browser_listener
from tests.unit.test_action_checks import document

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Browser opt-in required"),
]


@pytest.mark.parametrize("engine", os.getenv("RESPONSIVE_BROWSERS", "chromium").split(","))
def test_delayed_nicknames_conflicts_and_mobile_checklists(tmp_path, monkeypatch, engine):
    from playwright.sync_api import expect, sync_playwright

    doc = document()
    monkeypatch.setattr(
        "app.api.session.nmap_preflight", lambda config: (True, "Synthetic readiness")
    )
    monkeypatch.setattr("app.api.session.nmap_interface_choices", lambda config: [])
    JsonStore(os.environ["APP_DATA_DIR"])._create_scan(doc)
    original = JsonStore(os.environ["APP_DATA_DIR"])._scan_dir(doc.scan_id) / "scan.json"
    before = original.read_bytes()
    manager = SessionManager()
    listener = browser_listener()
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
        endpoint = base + f"/api/live-scans/{doc.scan_id}"
        with sync_playwright() as pw:
            browser = getattr(pw, engine).launch()
            ctx = browser.new_context(viewport={"width": 390, "height": 844})
            page = ctx.new_page()
            page.goto(manager.get_bootstrap_url(port))
            page.wait_for_function("!location.hash.includes('token=')")
            factual = ctx.request.get(endpoint).json()
            device = doc.devices[0].device_id
            revision = 1
            label = None
            held = []
            mode = "save"
            writes = []
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            # Advance only the nickname-poll timer, not API deadlines or workflow timers.
            page.add_init_script("""const originalTimeout = window.setTimeout.bind(window);
                window.setTimeout = (fn, ms, ...args) =>
                    originalTimeout(fn, ms === 8000 ? 100 : ms, ...args);""")

            def report(route):
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(
                        {
                            **factual,
                            "nickname_revision": revision,
                            "user_nicknames": {device: label} if label else {},
                        }
                    ),
                )

            def edit(route):
                nonlocal revision, label
                writes.append(route.request.post_data_json)
                if mode == "conflict":
                    revision, label = 4, "Other tab label"
                    route.fulfill(
                        status=409,
                        content_type="application/json",
                        body=json.dumps({"detail": "Nicknames changed; reload"}),
                    )
                else:
                    revision, label = 3, "Newest label"
                    route.fulfill(
                        status=200,
                        content_type="application/json",
                        body=json.dumps({"nickname_revision": revision}),
                    )

            page.route(endpoint, report)
            page.route(endpoint + f"/devices/{device}/nickname", edit)
            page.route(
                re.compile(re.escape(endpoint + "/nicknames") + r"(?:\?.*)?$"),
                lambda route: held.append(route),
            )
            page.goto(base + f"/scans/{doc.scan_id}")
            expect(page.locator("#comparison-summary")).not_to_be_empty()
            expect(page.locator(".next-step-checklist")).not_to_have_attribute("open", "")
            page.locator(".next-step-checklist > summary").first.click()
            expect(page.locator(".next-step-checklist select").first).to_be_visible()
            page.locator("#searchInput").fill(doc.devices[0].ip)
            page.locator("#device-summaries .device-summary > summary").first.click()
            deadline = time.monotonic() + 10
            while not held and time.monotonic() < deadline:
                page.wait_for_timeout(25)
            assert held
            page.get_by_role("button", name="Add your own nickname", exact=True).click()
            page.locator("#annotationEditorInput").fill("Newest label")
            page.locator("#annotationEditorSave").click()
            expect(page.locator("#device-summaries summary").first).to_contain_text("Newest label")
            held.pop(0).fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "revision": 2,
                        "changed": True,
                        "names": {device: "Delayed label"},
                        "recovery_notice": "Old recovery notice",
                    }
                ),
            )
            page.wait_for_timeout(150)
            expect(page.locator("#device-summaries summary").first).to_contain_text("Newest label")
            expect(page.locator("#result-status")).not_to_contain_text("Old recovery notice")
            expect(page.locator("#searchInput")).to_have_value(doc.devices[0].ip)
            expect(page.locator("#device-summaries .device-summary").first).to_have_attribute(
                "open", ""
            )
            assert writes[0]["expected_revision"] == 1
            # A rejected second-tab write reloads a fresh snapshot, never retries the write.
            mode = "conflict"
            page.get_by_role("button", name="Edit or remove your nickname", exact=True).focus()
            page.keyboard.press("Enter")
            page.locator("#annotationEditorInput").fill("Rejected label")
            page.locator("#annotationEditorSave").click()
            deadline = time.monotonic() + 10
            while len(writes) < 2 and time.monotonic() < deadline:
                page.wait_for_timeout(25)
            assert len(writes) == 2 and writes[1]["expected_revision"] == 3
            deadline = time.monotonic() + 10
            while not any(
                not route.request.url.endswith("?revision=3")
                and "?revision=" not in route.request.url
                for route in held
            ):
                assert time.monotonic() < deadline
                page.wait_for_timeout(25)
            for route in list(held):
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(
                        {"revision": 4, "changed": True, "names": {device: "Other tab label"}}
                    ),
                )
            held.clear()
            expect(page.locator("#device-summaries summary").first).to_contain_text(
                "Other tab label"
            )
            expect(page.locator("#result-status")).to_contain_text("was not saved")
            expect(page.locator("#result-status")).to_contain_text("Latest nicknames loaded")
            expect(page.locator("#annotationEditorInput")).to_have_value("Rejected label")
            expect(page.locator("#annotationEditorStatus")).to_contain_text("not saved")
            page.locator("#annotationEditorCancel").click()
            expect(
                page.get_by_role("button", name="Edit or remove your nickname", exact=True)
            ).to_be_focused()
            assert len(writes) == 2
            assert not errors
            page.screenshot(path=str(tmp_path / f"nickname-{engine}.png"))
            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth"), (
                page.evaluate(
                    """() => [...document.querySelectorAll('main *')]
                  .filter(e => e.getClientRects().length && !e.closest('.device-table-wrap')
                    && e.getBoundingClientRect().right > innerWidth + 1)
                  .map(e => ({tag:e.tagName,id:e.id,class:e.className,
                    right:e.getBoundingClientRect().right,
                    text:e.textContent.slice(0,120)})).slice(0,15)"""
                )
            )
            browser.close()
        assert original.read_bytes() == before
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        listener.close()
