"""Periodic-check UI uses intercepted fixtures only; no scheduler or scan runs."""

import os
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:54328"
pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browsers"),
]


@pytest.fixture(params=["chromium", "firefox"])
def viewer(request):
    from playwright.sync_api import sync_playwright

    html = (
        Environment(loader=FileSystemLoader(ROOT / "app/templates"), autoescape=select_autoescape())
        .get_template("settings.html")
        .render()
    )
    state = {
        "revision": 1,
        "enabled": False,
        "scope": None,
        "current_scope": "192.168.56.0/24",
        "interval_minutes": 60,
        "next_check_at": None,
        "last_scan_id": None,
        "last_outcome": None,
        "events": [],
        "pause_reason": None,
        "configuration_error": None,
        "available": True,
    }
    calls, errors, external = [], [], []
    faults = {"write": False, "read": False}
    with sync_playwright() as playwright:
        browser = getattr(playwright, request.param).launch(headless=True)
        page = browser.new_page(viewport={"width": 320, "height": 844}, reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("dialog", lambda dialog: dialog.accept())

        def intercept(route):
            req = route.request
            path = urlsplit(req.url).path
            if not req.url.startswith(BASE + "/"):
                external.append(req.url)
                route.abort()
            elif path == "/settings":
                route.fulfill(content_type="text/html", body=html)
            elif path == "/api/session":
                route.fulfill(json={"csrf_token": "synthetic-csrf"})
            elif path == "/api/monitoring" and req.method == "GET":
                if faults["read"]:
                    route.fulfill(status=503, json={"detail": "Synthetic status unavailable"})
                else:
                    route.fulfill(json=deepcopy(state))
            elif path == "/api/monitoring" and req.method == "PUT":
                body = req.post_data_json
                calls.append(body)
                assert req.headers.get("x-csrf-token") == "synthetic-csrf"
                if faults["write"]:
                    route.fulfill(status=409, json={"detail": "Synthetic version conflict"})
                    return
                assert body["expected_revision"] == state["revision"]
                assert (
                    not body["enabled"]
                    or body["authorised"]
                    and body["confirmed_scope"] == state["current_scope"]
                )
                state.update(
                    revision=state["revision"] + 1,
                    enabled=body["enabled"],
                    interval_minutes=body["interval_minutes"],
                    scope=body["confirmed_scope"] if body["enabled"] else state["scope"],
                    next_check_at="2026-10-14T19:00:00Z" if body["enabled"] else None,
                )
                route.fulfill(json=deepcopy(state))
            elif path == "/api/settings":
                assert req.method == "GET", "Editing network settings is outside this test"
                route.fulfill(
                    json={
                        "revision": 1,
                        "allowed_network": None,
                        "interface": None,
                        "retain_raw_xml": False,
                        "mdns_enabled": False,
                        "ai_enabled": True,
                    }
                )
            elif path == "/api/status":
                route.fulfill(
                    json={
                        "allowed_network": state["current_scope"],
                        "scope_source": "automatic",
                        "detected_network": state["current_scope"],
                        "interface_choices": [],
                        "mdns_available": False,
                        "ai_available": False,
                    }
                )
            elif path.startswith("/static/"):
                asset = (ROOT / "app" / path.lstrip("/")).resolve()
                assert asset.is_relative_to((ROOT / "app/static").resolve())
                route.fulfill(
                    body=asset.read_bytes(),
                    content_type="text/css" if asset.suffix == ".css" else "text/javascript",
                )
            else:
                external.append(req.url)
                route.abort()

        page.route("**/*", intercept)
        page.goto(BASE + "/settings")
        from playwright.sync_api import expect

        expect(page.locator("#monitor-summary")).to_contain_text("checks are off")
        yield page, state, calls, faults
        assert errors == [] and external == []
        browser.close()


def test_opt_in_stop_and_network_edit_require_explicit_permission(viewer):
    from playwright.sync_api import expect

    page, state, calls, _faults = viewer
    page.locator("#monitor-interval").select_option("30")
    expect(page.locator("#monitor-start")).to_be_disabled()
    assert calls == []
    page.locator("#monitor-authorised").check()
    page.locator("#monitor-start").click()
    expect(page.locator("#monitor-summary")).to_contain_text("are enabled")
    assert calls[0]["authorised"] is True
    expect(page.locator("#monitor-authorised")).not_to_be_checked()
    page.locator("#scope-mode").select_option("manual")
    expect(page.locator("#monitor-start")).to_be_disabled()
    expect(page.locator("#monitor-stop")).to_be_enabled()
    page.locator("#monitor-stop").click()
    expect(page.locator("#monitor-summary")).to_contain_text("checks are off")
    assert calls[-1]["authorised"] is False and state["enabled"] is False
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_conflicts_preserve_draft_and_read_outage_never_enables_checks(viewer):
    from playwright.sync_api import expect

    page, _state, calls, faults = viewer
    page.locator("#monitor-interval").select_option("360")
    page.locator("#monitor-authorised").check()
    faults["write"] = True
    page.locator("#monitor-start").click()
    expect(page.locator("#monitor-error")).to_contain_text("Reload periodic-check status")
    expect(page.locator("#monitor-interval")).to_have_value("360")
    expect(page.locator("#monitor-start")).to_be_disabled()
    faults["read"] = True
    page.locator("#monitor-reload").click()
    expect(page.locator("#monitor-error")).to_contain_text("Synthetic status unavailable")
    expect(page.locator("#monitor-authorised")).not_to_be_checked()
    assert len(calls) == 1


def test_scope_reload_clears_permission_and_controls_reflow_in_both_themes(viewer):
    from playwright.sync_api import expect

    page, state, calls, _faults = viewer
    page.locator("#monitor-authorised").check()
    state["current_scope"] = "10.2.3.0/24"
    page.locator("#monitor-reload").click()
    expect(page.locator("#monitor-scope")).to_contain_text("10.2.3.0/24")
    expect(page.locator("#monitor-authorised")).not_to_be_checked()
    expect(page.locator("#monitor-start")).to_be_disabled()
    for theme in ("dark", "light"):
        page.locator("#themePreference").select_option(theme)
        for width in (320, 768, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert page.locator("#monitor-interval").bounding_box()["height"] >= 44
    assert calls == []
