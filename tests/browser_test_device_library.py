"""Serverless browser checks: every page, asset and API response is intercepted."""

import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browser"),
]
ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "http://127.0.0.1:54329"


def key(index):
    return f"d-{index:064x}"


def device(index):
    return {
        "device_key": key(index),
        "display_name": f"Household device {index}",
        "last_ip": f"192.168.56.{index}",
        "network": "192.168.56.0/24",
        "first_observed": "2026-10-10T09:00:00Z",
        "last_observed": "2026-10-14T09:00:00Z",
        "report_count": 1,
        "review_count": 2,
        "unfinished_count": 0,
        "reports": [
            {
                "scan_id": "00000000-0000-4000-8000-000000000001",
                "device_id": "synthetic-device",
                "created_at": "2026-10-14T09:00:00Z",
                "state": "completed",
            }
        ],
        "annotations": {"room": "", "favourite": False, "recognised": False},
        "editable": True,
    }


@pytest.fixture
def viewer():
    from playwright.sync_api import sync_playwright

    environment = Environment(
        loader=FileSystemLoader(ROOT / "app/templates"), autoescape=select_autoescape()
    )
    html = environment.get_template("devices.html").render()
    with sync_playwright() as playwright:
        browsers = []

        def create(engine, count=30):
            browser = getattr(playwright, engine).launch(headless=True)
            browsers.append(browser)
            page = browser.new_page(viewport={"width": 320, "height": 568}, reduced_motion="reduce")
            state = {
                "items": [device(index + 1) for index in range(count)],
                "revision": 1,
                "fault": None,
                "reads": [],
                "writes": [],
                "unexpected": [],
                "errors": [],
            }
            page.on("pageerror", lambda error: state["errors"].append(str(error)))
            page.on("dialog", lambda dialog: dialog.accept())

            def intercept(route):
                request = route.request
                parts = urlsplit(request.url)
                if not request.url.startswith(ORIGIN + "/"):
                    state["unexpected"].append(request.url)
                    route.abort()
                    return
                if parts.path == "/devices":
                    route.fulfill(content_type="text/html", body=html)
                elif parts.path == "/api/session" and request.method == "GET":
                    route.fulfill(json={"csrf_token": "synthetic-csrf"})
                elif parts.path == "/api/devices" and request.method == "GET":
                    params = parse_qs(parts.query)
                    offset = int(params.get("offset", ["0"])[0])
                    limit = int(params.get("limit", ["24"])[0])
                    query = params.get("search", [""])[0]
                    view = params.get("view", ["all"])[0]
                    state["reads"].append(
                        {"offset": offset, "limit": limit, "search": query, "view": view}
                    )
                    if state["fault"] == "load":
                        route.fulfill(status=503, json={"detail": "Synthetic list outage"})
                        return
                    matches = [
                        item
                        for item in state["items"]
                        if all(
                            word
                            in (
                                item["display_name"]
                                + " "
                                + item["last_ip"]
                                + " "
                                + item["annotations"]["room"]
                            ).casefold()
                            for word in query.casefold().split()
                        )
                    ]
                    if state["fault"] != "old-view" and view != "all":
                        matches = [
                            item
                            for item in matches
                            if {
                                "favourites": item["annotations"]["favourite"],
                                "not-recognised": not item["annotations"]["recognised"],
                                "unfinished": item["unfinished_count"] > 0,
                                "review": item["review_count"] > 0,
                            }[view]
                        ]
                    route.fulfill(
                        json={
                            "items": matches[offset : offset + limit],
                            "total": len(matches),
                            "offset": offset,
                            "limit": limit,
                            "revision": state["revision"],
                            "warnings": [],
                            "view": "all" if state["fault"] == "old-view" else view,
                        }
                    )
                elif parts.path.startswith("/api/devices/d-") and request.method == "PUT":
                    payload = request.post_data_json
                    state["writes"].append(payload)
                    assert request.headers.get("x-csrf-token") == "synthetic-csrf"
                    if state["fault"] == "save":
                        route.fulfill(status=409, json={"detail": "Saved labels changed"})
                        return
                    item = next(
                        item
                        for item in state["items"]
                        if item["device_key"] == parts.path.rsplit("/", 1)[1]
                    )
                    assert payload["expected_revision"] == state["revision"]
                    item["annotations"] = {
                        field: payload[field] for field in ("room", "favourite", "recognised")
                    }
                    state["revision"] += 1
                    route.fulfill(
                        json={
                            "device_key": item["device_key"],
                            "annotations": item["annotations"],
                            "revision": state["revision"],
                            "editable": True,
                        }
                    )
                elif parts.path.startswith("/static/"):
                    path = (ROOT / "app" / parts.path.lstrip("/")).resolve()
                    static = (ROOT / "app/static").resolve()
                    assert path.is_relative_to(static)
                    mime = "text/css" if path.suffix == ".css" else "text/javascript"
                    route.fulfill(content_type=mime, body=path.read_bytes())
                elif parts.path == "/favicon.ico":
                    route.fulfill(status=204)
                else:
                    state["unexpected"].append(request.url)
                    route.abort()

            page.route("**/*", intercept)
            return page, state

        yield create
        for browser in browsers:
            browser.close()


@pytest.mark.parametrize("engine", os.getenv("UI_UX_BROWSERS", "chromium").split(","))
def test_device_inventory_complete_pages_search_and_reflow(engine, viewer):
    from playwright.sync_api import expect

    page, state = viewer(engine)
    state["items"][0]["display_name"] = '<img src="https://invalid.example/" onerror="alert(1)">'
    page.goto(ORIGIN + "/devices")
    expect(page.locator(".device-library-card")).to_have_count(24)
    assert len(state["reads"]) == 1
    expect(page.locator(".device-library-card").first.locator("h3")).to_have_text(
        state["items"][0]["display_name"]
    )
    assert page.locator(".device-library-card img").count() == 0
    page.keyboard.press("End")
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(resolve))")
    assert len(state["reads"]) == 1
    page.locator("#device-library-pages-bottom").get_by_role("button", name="Next page").click()
    expect(page.locator(".device-library-card")).to_have_count(6)
    assert state["reads"][-1] == {"offset": 24, "limit": 24, "search": "", "view": "all"}
    assert page.evaluate("document.activeElement.id") == "device-library-heading"
    assert "page 2 of 2" in page.title()
    page.get_by_role("searchbox", name="Search saved devices").fill("Household device 29")
    page.get_by_role("button", name="Search devices", exact=True).click()
    expect(page.locator(".device-library-card")).to_have_count(1)
    expect(page.locator(".device-library-card h3")).to_have_text("Household device 29")
    assert state["reads"][-1]["offset"] == 0
    page.get_by_role("searchbox", name="Search saved devices").fill("no such device")
    page.get_by_role("button", name="Search devices", exact=True).click()
    expect(page.locator("#device-library-empty-title")).to_have_text(
        "No saved devices match this search and view"
    )
    page.get_by_role("button", name="Reset search and view", exact=True).click()
    expect(page.locator(".device-library-card")).to_have_count(24)
    card = page.locator(".device-library-card").nth(1)
    card.get_by_text("Your household labels", exact=True).click()
    for theme in ("light", "dark"):
        page.evaluate(
            "theme => window.NetGuardAppearance.applyAppearancePreferences({theme})", theme
        )
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    for selector in ("input[type=text]", "button[type=submit]", "button[type=button]"):
        for control in card.locator(selector).all():
            if control.is_visible():
                assert control.bounding_box()["height"] >= 44
    assert not state["unexpected"]
    assert not state["errors"]
    assert not state["writes"]


@pytest.mark.parametrize("engine", os.getenv("UI_UX_BROWSERS", "chromium").split(","))
def test_device_labels_conflict_reload_and_explicit_save_keep_draft(engine, viewer):
    from playwright.sync_api import expect

    page, state = viewer(engine, count=1)
    page.goto(ORIGIN + "/devices")
    card = page.locator(".device-library-card")
    expect(card).to_have_count(1)
    card.get_by_text("Your household labels", exact=True).click()
    room = card.get_by_role("textbox", name="Your room or location")
    room.fill("Study\u200b")
    expect(room).to_have_attribute("aria-invalid", "true")
    expect(card.get_by_role("button", name="Save household labels", exact=True)).to_be_disabled()
    assert not state["writes"]
    room.fill("My Study")
    card.get_by_label("Keep as my favourite", exact=True).check()
    card.get_by_label("I recognise this device (my label, not a safety check)").check()
    state["fault"] = "save"
    card.get_by_role("button", name="Save household labels", exact=True).click()
    expect(card.locator("[role=status]")).to_contain_text("Your draft is kept")
    expect(room).to_have_value("My Study")
    expect(card.get_by_role("button", name="Save household labels", exact=True)).to_be_disabled()
    assert len(state["writes"]) == 1
    state["fault"] = None
    state["revision"] = 2
    state["items"][0]["annotations"]["room"] = "Other saved room"
    card.get_by_role("button", name="Reload saved labels, keep draft").click()
    expect(card.locator(".device-library-saved-labels")).to_contain_text("Other saved room")
    expect(room).to_have_value("My Study")
    expect(card.get_by_role("button", name="Save household labels", exact=True)).to_be_enabled()
    card.get_by_role("button", name="Save household labels", exact=True).click()
    expect(card.locator("[role=status]")).to_contain_text("Household labels saved")
    assert state["writes"][-1] == {
        "expected_revision": 2,
        "room": "My Study",
        "favourite": True,
        "recognised": True,
    }
    assert state["items"][0]["last_ip"] == "192.168.56.1"
    expect(card.locator(".device-library-badges")).to_contain_text("not verified")
    assert page.evaluate("document.activeElement.id").startswith("label-status-")
    page.reload()
    expect(page.locator(".device-library-badges")).to_contain_text("My Study")
    assert not state["unexpected"]
    assert not state["errors"]


@pytest.mark.parametrize("engine", os.getenv("UI_UX_BROWSERS", "chromium").split(","))
def test_device_list_outage_retry_and_readonly_evidence(engine, viewer):
    from playwright.sync_api import expect

    page, state = viewer(engine, count=2)
    state["fault"] = "load"
    page.goto(ORIGIN + "/devices")
    expect(page.locator("#device-library-error")).to_contain_text("Synthetic list outage")
    assert len(state["reads"]) == 1
    state["fault"] = None
    state["revision"] = None
    for item in state["items"]:
        item["editable"] = False
    state["items"][0]["identity_note"] = "Selected address only; a response was not established."
    state["items"][0]["reports"][0]["device_id"] = None
    page.get_by_role("button", name="Retry loading devices").click()
    expect(page.locator(".device-library-card")).to_have_count(2)
    card = page.locator(".device-library-card").first
    card.get_by_text("Your household labels", exact=True).click()
    expect(card.locator(".device-library-saved-labels")).to_contain_text("not confirmed")
    expect(card.get_by_role("textbox", name="Your room or location")).to_be_disabled()
    card.get_by_text("Open recorded reports", exact=True).click()
    expect(card.get_by_role("link")).to_have_attribute(
        "href", "/scans/00000000-0000-4000-8000-000000000001"
    )
    expect(card).to_contain_text("a response was not established")
    device_card = page.locator(".device-library-card").nth(1)
    device_card.get_by_text("Open recorded reports", exact=True).click()
    expect(device_card.get_by_role("link")).to_have_attribute(
        "href", "/scans/00000000-0000-4000-8000-000000000001#devices-title"
    )
    expect(card).to_contain_text("current connection status is unknown")
    assert len(state["reads"]) == 2
    assert not state["writes"]
    assert not state["unexpected"]
    assert not state["errors"]


@pytest.mark.parametrize("engine", os.getenv("UI_UX_BROWSERS", "chromium").split(","))
def test_device_views_apply_deliberately_across_pages_and_reset(engine, viewer):
    from playwright.sync_api import expect

    page, state = viewer(engine, count=30)
    for index, item in enumerate(state["items"]):
        item["annotations"]["favourite"] = index % 2 == 0
        item["annotations"]["recognised"] = index != 28
        item["unfinished_count"] = int(index == 29)
    page.goto(ORIGIN + "/devices")
    expect(page.locator(".device-library-card")).to_have_count(24)
    select = page.get_by_role("combobox", name="Show saved devices")
    select.select_option("favourites")
    assert len(state["reads"]) == 1
    page.get_by_role("button", name="Search devices", exact=True).click()
    expect(page.locator(".device-library-card")).to_have_count(15)
    expect(page.locator("#device-library-applied")).to_contain_text("My favourites")
    assert state["reads"][-1]["offset"] == 0
    select.select_option("not-recognised")
    page.get_by_role("button", name="Search devices", exact=True).click()
    expect(page.locator(".device-library-card")).to_have_count(1)
    expect(page.locator(".device-library-card h3")).to_have_text("Household device 29")
    select.select_option("unfinished")
    page.get_by_role("button", name="Search devices", exact=True).click()
    expect(page.locator(".device-library-card h3")).to_have_text("Household device 30")
    page.get_by_role("searchbox", name="Search saved devices").fill("not-a-device")
    page.get_by_role("button", name="Search devices", exact=True).click()
    expect(page.locator("#device-library-empty")).to_be_visible()
    expect(page.locator("#device-library-empty-help")).to_contain_text("does not mean")
    page.get_by_role("button", name="Reset search and view", exact=True).click()
    expect(page.locator(".device-library-card")).to_have_count(24)
    expect(select).to_have_value("all")
    assert state["reads"][-1]["view"] == "all"
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    assert not state["writes"] and not state["errors"] and not state["unexpected"]


@pytest.mark.parametrize("engine", os.getenv("UI_UX_BROWSERS", "chromium").split(","))
def test_ignored_view_retains_draft_and_explains_legacy_backend(engine, viewer):
    from playwright.sync_api import expect

    page, state = viewer(engine, count=1)
    page.goto(ORIGIN + "/devices")
    card = page.locator(".device-library-card")
    expect(card).to_have_count(1)
    card.get_by_text("Your household labels", exact=True).click()
    room = card.get_by_role("textbox", name="Your room or location")
    room.fill("Unsaved Study")
    state["fault"] = "old-view"
    page.get_by_role("combobox", name="Show saved devices").select_option("favourites")
    page.get_by_role("button", name="Search devices", exact=True).click()
    expect(page.locator("#device-library-error")).to_contain_text("restart the backend")
    expect(room).to_have_value("Unsaved Study")
    expect(page.locator("#device-library-applied")).to_contain_text("All devices")
    assert not state["writes"] and not state["errors"] and not state["unexpected"]
