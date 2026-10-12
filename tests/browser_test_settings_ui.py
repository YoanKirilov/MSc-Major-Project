"""Offline shared-shell and form tasks; writes/providers are synthetic only."""

import json
import os
import threading
import time

import pytest
import uvicorn
from app.main import create_app
from app.security.session import SessionManager
from tests.fixtures.browser import browser_listener

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in UI browser tasks"),
]


@pytest.mark.parametrize("engine", os.getenv("UI_UX_BROWSERS", "chromium").split(","))
def test_settings_history_errors_scope_focus_and_shared_shell(engine, monkeypatch):
    from playwright.sync_api import expect, sync_playwright

    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    monkeypatch.setattr("app.api.session.nmap_preflight", lambda config: (True, "synthetic"))
    monkeypatch.setattr("app.api.session.nmap_interface_choices", lambda config: [])
    monkeypatch.setattr("app.api.settings.nmap_interface_choices", lambda config: [])
    monkeypatch.setattr("app.api.session.detect_private_network", lambda: "192.168.56.0/24")

    async def unavailable(self):
        return False

    monkeypatch.setattr(
        "app.explanations.service.ExplanationService.provider_available", unavailable
    )
    manager = SessionManager()
    listener = browser_listener()
    port = listener.getsockname()[1]
    monkeypatch.setenv("APP_PORT", str(port))
    server = uvicorn.Server(uvicorn.Config(create_app(session_manager=manager), log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    errors, dialogs, updates, external = [], [], [], []
    fault = {"settings_get": False, "status": False, "save_status": 409}
    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started
        base = f"http://127.0.0.1:{port}"
        with sync_playwright() as playwright:
            browser = getattr(playwright, engine).launch(headless=True)
            page = browser.new_page(viewport={"width": 320, "height": 568}, reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))

            def dialog_seen(dialog):
                dialogs.append(dialog.message)
                dialog.dismiss()

            page.on("dialog", dialog_seen)

            def intercept(route):
                request = route.request
                if not request.url.startswith(base + "/"):
                    external.append(request.url)
                    route.abort()
                    return
                if request.method == "POST" and request.url.endswith("/api/live-scans"):
                    raise AssertionError("Viewing or editing forms must not start a scan")
                if request.method == "PATCH" and request.url.endswith("/api/settings"):
                    updates.append(request.post_data_json)
                    detail = (
                        "Settings changed; reload and try again"
                        if fault["save_status"] == 409
                        else "Network range: enter a valid private IPv4 CIDR"
                    )
                    route.fulfill(
                        status=fault["save_status"],
                        content_type="application/json",
                        body=json.dumps({"detail": detail}),
                    )
                    return
                if (
                    request.method == "GET"
                    and request.url.endswith("/api/settings")
                    and fault["settings_get"]
                ) or (request.url.endswith("/api/status") and fault["status"]):
                    route.fulfill(
                        status=503,
                        content_type="application/json",
                        body=json.dumps({"detail": "Synthetic temporary outage"}),
                    )
                    return
                route.continue_()

            page.route("**/*", intercept)
            page.goto(manager.get_bootstrap_url(port))
            page.wait_for_function("sessionStorage.getItem('network-assessor-csrf') !== null")
            expect(page.locator("#scanLaunchButton")).to_be_enabled()
            page.wait_for_function("document.querySelector('#runningScans').dataset.snapshot")
            page.goto(base + "/settings")
            expect(page.locator("#save-settings")).to_be_enabled()
            expect(page.locator("#manual-network-field")).to_be_hidden()
            expect(page.locator("#allowed-network")).to_be_disabled()
            assert page.locator("h1").count() == 1
            assert page.title().startswith("Settings")
            expect(page.locator("nav a[aria-current=page]")).to_have_text("Settings")
            expect(page.locator("#network-status")).to_contain_text("backend configuration")
            page.locator(".skip-link").focus()
            page.keyboard.press("Enter")
            assert page.evaluate("document.activeElement.id") == "main-content"
            page.locator("#scope-mode").select_option("manual")
            page.locator("#allowed-network").fill("invalid")
            page.locator("#save-settings").click()
            expect(page.locator("#settings-errors")).to_be_visible()
            expect(page.locator("#allowed-network-error")).to_contain_text("IPv4")
            expect(page.locator("#allowed-network")).to_have_attribute("aria-invalid", "true")
            assert page.evaluate("document.activeElement.id") == "settings-errors"
            assert not updates
            page.locator("#settings-error-list a").click()
            assert page.evaluate("document.activeElement.id") == "allowed-network"
            for value in (
                "192.168.56.5/24",
                "8.8.8.0/24",
                "192.168.056.0/24",
                "192.168.56.0/23",
            ):
                page.locator("#allowed-network").fill(value)
                page.locator("#save-settings").click()
                expect(page.locator("#allowed-network-error")).to_be_visible()
            assert not updates
            page.locator("#allowed-network").fill("192.168.56.0/24")
            page.locator("#save-settings").click()
            expect(page.locator("#settings-errors")).to_contain_text("input is unchanged")
            expect(page.locator("#allowed-network")).to_have_value("192.168.56.0/24")
            expect(page.locator("#reload-settings")).to_be_visible()
            assert len(updates) == 1
            page.locator("#reload-settings").click()
            expect(page.locator("#scope-mode")).to_have_value("automatic")
            expect(page.locator("#save-settings")).to_be_enabled()

            fault["save_status"] = 422
            page.locator("#scope-mode").select_option("manual")
            page.locator("#allowed-network").fill("192.168.56.0/24")
            page.locator("#save-settings").click()
            expect(page.locator("#allowed-network-error")).to_contain_text("Network range")
            expect(page.locator("#allowed-network")).to_have_value("192.168.56.0/24")
            assert page.evaluate("document.activeElement.id") == "settings-errors"

            fault["status"] = True
            page.goto(base + "/settings")
            expect(page.locator("#save-settings")).to_be_enabled()
            expect(page.locator("#network-status")).to_contain_text("could not be checked")
            page.locator(".settings-advanced").evaluate("element => element.open = true")
            expect(page.locator("#mdns-status")).to_contain_text("could not be checked")
            expect(page.locator("#pihole-status")).to_contain_text("could not be checked")
            fault["status"] = False
            fault["settings_get"] = True
            page.goto(base + "/settings")
            expect(page.locator("#settings-errors")).to_contain_text("could not be loaded")
            expect(page.locator("#save-settings")).to_be_disabled()
            expect(page.locator("#reload-settings")).to_be_visible()
            fault["settings_get"] = False
            page.locator("#reload-settings").click()
            expect(page.locator("#save-settings")).to_be_enabled()

            page.goto(base + "/history")
            expect(page.locator("#history-status")).to_contain_text("No saved reports yet")
            expect(page.locator("#history-empty")).to_be_visible()
            assert page.title().startswith("Saved reports")
            expect(page.locator("nav a[aria-current=page]")).to_have_text("Saved reports")
            page.locator("#history-after").fill("2026-10-08")
            page.locator("#history-before").fill("2026-10-01")
            page.get_by_role("button", name="Search reports", exact=True).click()
            expect(page.locator("#history-filter-error")).to_contain_text("To date")
            assert page.evaluate("document.activeElement.id") == "history-filter-error"
            expect(page.locator("#history-before")).to_have_attribute("aria-invalid", "true")
            page.get_by_role("button", name="Clear filters", exact=True).click()
            expect(page.locator("#history-filter-error")).to_be_hidden()
            expect(page.locator("#history-status")).to_contain_text("No saved reports yet")
            for width, height in ((320, 568), (390, 844), (768, 1024), (1440, 1000)):
                page.set_viewport_size({"width": width, "height": height})
                for route in ("/settings", "/history", "/light", "/deep"):
                    page.goto(base + route)
                    # Measure a populated page, not a form or picker still loading.
                    # Rapid synthetic navigation can cancel WebKit's initial fetches.
                    if route == "/settings":
                        expect(page.locator("#save-settings")).to_be_enabled()
                    elif route == "/history":
                        expect(page.locator("#history-status")).to_contain_text(
                            "No saved reports yet"
                        )
                    else:
                        expect(page.locator("#scanLaunchButton")).to_be_enabled()
                        page.wait_for_function(
                            "document.querySelector('#runningScans').dataset.snapshot"
                        )
                        if route == "/deep":
                            expect(page.locator("#recentDeviceNote")).not_to_be_empty()
                    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth"), (
                        json.dumps(
                            page.evaluate("""() => ({viewport:innerWidth,
                          scrollWidth:document.documentElement.scrollWidth,
                          bodyScrollWidth:document.body.scrollWidth,
                          layout:[...document.querySelectorAll(
                            'main, form, fieldset, details, .card, .form-field, select')]
                            .map(e => ({tag:e.tagName,id:e.id,class:e.className,
                              scroll:e.scrollWidth,client:e.clientWidth,
                              width:e.getBoundingClientRect().width,
                              right:e.getBoundingClientRect().right,
                              display:getComputedStyle(e).display})),
                          elements:[...document.querySelectorAll('body *')]
                            .filter(e => e.getClientRects().length
                              && e.getBoundingClientRect().right > innerWidth-.1)
                            .map(e => ({tag:e.tagName,id:e.id,class:e.className,
                              width:e.getBoundingClientRect().width,
                              right:e.getBoundingClientRect().right,
                              text:e.textContent.slice(0,60)})).slice(0,30)})""")
                        )
                    )
            assert not errors and not dialogs and not external
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=15)
