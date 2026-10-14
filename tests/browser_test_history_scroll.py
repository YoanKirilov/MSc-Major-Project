"""Paged saved-report browsing; mocked list/deletion API, no device traffic."""

import os
import threading
import time
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest
import uvicorn
from app.main import create_app
from app.security.session import SessionManager
from tests.fixtures.browser import browser_listener

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browser"),
]
ENGINES = os.getenv("UI_UX_BROWSERS", "chromium").split(",")


@pytest.fixture(params=ENGINES)
def history_browser(request, monkeypatch, tmp_path):
    from playwright.sync_api import sync_playwright

    listener = browser_listener()
    port = listener.getsockname()[1]
    monkeypatch.setenv("APP_PORT", str(port))
    manager = SessionManager()
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(session_manager=manager),
            log_level="error",
            timeout_graceful_shutdown=1,
        )
    )
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    context = browser = None
    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started
        base = f"http://127.0.0.1:{port}"
        with sync_playwright() as playwright:
            browser = getattr(playwright, request.param).launch(headless=True)
            try:
                context = browser.new_context(
                    viewport={"width": 1280, "height": 900}, reduced_motion="reduce"
                )
                context.add_cookies(
                    [{"name": "session_id", "value": manager.register_session(), "url": base}]
                )
                calls, errors, forbidden = [], [], []
                reports = [
                    {
                        "scan_id": str(uuid4()),
                        "storage_status": "ok",
                        "source": "live",
                        "title": f"Saved report {index + 1}",
                        "profile": ["light", "deep-tcp-v1", "unknown"][index % 3],
                        "state": "completed",
                        "created_at": "2026-10-12T10:00:00Z",
                        "device_count": 2,
                        "finding_count": 1,
                        "revision": 2,
                        "expected_notes_revision": 1,
                        "phase": "finished",
                        "deletable": True,
                    }
                    for index in range(53)
                ]
                controls = {
                    "fail_offset": None,
                    "fail_query": None,
                    "empty_offset": None,
                    "report_count": 53,
                    "hold_offset": None,
                    "held_page": None,
                    "unreadable_offset": None,
                    "reports": reports,
                    "deleted": set(),
                    "delete_calls": [],
                    "delete_failure": False,
                    "delete_results": {},
                    "hold_delete": False,
                    "held_delete": None,
                    "trash": {},
                    "restore_calls": [],
                    "restore_failure": False,
                    "duplicate_offset": None,
                    "artifact_dir": tmp_path,
                }

                def route_request(route):
                    url = urlsplit(route.request.url)
                    if url.hostname != "127.0.0.1":
                        forbidden.append(route.request.url)
                        route.abort()
                        return
                    if url.path == "/api/reports/delete" and route.request.method == "POST":
                        body = route.request.post_data_json
                        controls["delete_calls"].append(body)
                        assert list(body) == ["reports"]
                        assert 1 <= len(body["reports"]) <= 24
                        valid_ids = {report["scan_id"] for report in reports}
                        assert all(
                            item["scan_id"] in valid_ids
                            and item["expected_revision"] == 2
                            and item["expected_notes_revision"] == 1
                            for item in body["reports"]
                        )
                        if controls["delete_failure"]:
                            route.fulfill(
                                status=503, json={"detail": "Synthetic delete unavailable."}
                            )
                            return
                        results = []
                        for item in body["reports"]:
                            scan_id = item["scan_id"]
                            status = controls["delete_results"].get(scan_id, "deleted")
                            results.append(
                                {
                                    "scan_id": scan_id,
                                    "status": status,
                                    "message": "Report moved to private trash."
                                    if status == "deleted"
                                    else "This report was not removed.",
                                }
                            )
                            if status == "deleted":
                                trash_id = str(uuid4())
                                results[-1]["trash_id"] = trash_id
                                controls["trash"][trash_id] = scan_id
                        payload = {
                            "results": results,
                            "deleted_count": sum(item["status"] == "deleted" for item in results),
                            "recoverable": True,
                        }
                        for result in results:
                            if result["status"] == "deleted":
                                controls["deleted"].add(result["scan_id"])
                        if controls["hold_delete"]:
                            controls["held_delete"] = (route, payload)
                        else:
                            route.fulfill(json=payload)
                        return
                    if url.path == "/api/reports/restore" and route.request.method == "POST":
                        body = route.request.post_data_json
                        controls["restore_calls"].append(body)
                        assert list(body) == ["trash_ids"]
                        assert 1 <= len(body["trash_ids"]) <= 24
                        assert all(trash_id in controls["trash"] for trash_id in body["trash_ids"])
                        if controls["restore_failure"]:
                            route.fulfill(
                                status=503, json={"detail": "Synthetic restore unavailable."}
                            )
                            return
                        results = []
                        for trash_id in body["trash_ids"]:
                            scan_id = controls["trash"][trash_id]
                            controls["deleted"].discard(scan_id)
                            results.append(
                                {
                                    "trash_id": trash_id,
                                    "scan_id": scan_id,
                                    "status": "restored",
                                    "message": "Report restored.",
                                }
                            )
                        route.fulfill(json={"results": results, "restored_count": len(results)})
                        return
                    if url.path == "/api/reports/recovery" and route.request.method == "GET":
                        params = parse_qs(url.query)
                        offset = int(params.get("offset", ["0"])[0])
                        items = [
                            {
                                **next(
                                    report for report in reports if report["scan_id"] == scan_id
                                ),
                                "trash_id": trash_id,
                                "restorable": True,
                                "bytes": 1000,
                                "removed_at": "2026-10-14T09:00:00Z",
                            }
                            for trash_id, scan_id in controls["trash"].items()
                            if scan_id in controls["deleted"]
                        ]
                        route.fulfill(
                            json={
                                "items": items[offset : offset + 24],
                                "total": len(items),
                                "warnings": [],
                            }
                        )
                        return
                    if route.request.method != "GET":
                        forbidden.append(route.request.url)
                        route.abort()
                        return
                    if url.path == "/api/reports":
                        params = parse_qs(url.query)
                        calls.append(params)
                        offset = int(params.get("offset", [0])[0])
                        limit = int(params.get("limit", [24])[0])
                        assert limit == 24
                        query = params.get("q", [""])[0]
                        if controls["fail_offset"] == offset or controls["fail_query"] == query:
                            route.fulfill(status=503, json={"detail": "Synthetic local failure."})
                            return
                        matches = [
                            report
                            for report in reports[: controls["report_count"]]
                            if query.casefold() in report["title"].casefold()
                            and report["scan_id"] not in controls["deleted"]
                            and (
                                not params.get("profile")
                                or report["profile"] == params["profile"][0]
                            )
                            and (not params.get("state") or report["state"] == params["state"][0])
                        ]
                        payload = {
                            "items": []
                            if controls["empty_offset"] == offset
                            else matches[offset : offset + limit],
                            "total": len(matches),
                            "warnings": [],
                            "unreadable_count": 0,
                        }
                        if controls["unreadable_offset"] == offset:
                            payload["items"][0] = {
                                **payload["items"][0],
                                "storage_status": "unreadable",
                                "deletable": False,
                            }
                            payload["unreadable_count"] = 1
                            payload["warnings"] = [
                                "One saved report could not be read. Its files are preserved."
                            ]
                        if controls["duplicate_offset"] == offset and len(payload["items"]) > 1:
                            payload["items"][1] = payload["items"][0]
                        if controls["hold_offset"] == offset:
                            controls["held_page"] = (route, payload)
                            return
                        route.fulfill(json=payload)
                        return
                    route.continue_()

                context.route("**/*", route_request)
                page = context.new_page()
                page.on("pageerror", lambda error: errors.append(str(error)))
                yield page, base, calls, controls
                assert not errors
                assert not forbidden
            finally:
                # Each fixture owns a fresh browser, with no HAR/video recording.
                # Closing it directly avoids Firefox's context-removal session-store
                # race and keeps cleanup inside the live Playwright event loop.
                browser.close()
                browser = None
                context = None
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        listener.close()


def wait_for_page(page, count=24):
    from playwright.sync_api import expect

    expect(page.locator("#history-list > li")).to_have_count(count)
    expect(page.locator("#history-scroll-stage")).to_have_attribute("data-phase", "ready")


@pytest.mark.parametrize("total", [0, 1, 23, 24, 25, 53])
def test_complete_initial_page_has_no_gesture_requirement(history_browser, total):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    controls["report_count"] = total
    page.goto(base + "/history")
    wait_for_page(page, min(total, 24))
    assert len(calls) == 1 and calls[0]["limit"] == ["24"]
    expect(page.locator("#history-pagination")).to_be_visible() if total > 24 else expect(
        page.locator("#history-pagination")
    ).to_be_hidden()
    if total == 0:
        expect(page.locator("#history-empty")).to_be_visible()
    assert page.locator("#history-sentinel, #history-scroll-link").count() == 0


def test_end_scrollbar_jump_find_and_resize_never_leave_unrendered_rows(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")
    wait_for_page(page)
    page.locator("#history-status").focus()
    page.keyboard.press("End")
    page.wait_for_timeout(100)
    assert len(calls) == 1
    wait_for_page(page)
    page.evaluate("window.scrollTo(0, 0)")
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.set_viewport_size({"width": 1440, "height": 1600})
    wait_for_page(page)
    # Ordinary native text exists independently of observation/scroll callbacks.
    assert page.evaluate(
        "document.querySelector('#history-list').innerText.includes('Saved report 24')"
    )
    row = page.locator("#history-list > li").last
    row.locator("a").focus()
    expect(row.locator("a")).to_be_focused()
    assert row.evaluate("node => getComputedStyle(node).opacity") == "1"
    assert row.get_attribute("hidden") is None
    assert len(calls) == 1
    expect(page.locator("#history-pagination-bottom")).to_be_visible()


@pytest.mark.parametrize("observer", ["absent", "throws"])
def test_observer_failure_only_removes_optional_animation(history_browser, observer):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.add_init_script(
        "window.IntersectionObserver = undefined"
        if observer == "absent"
        else "window.IntersectionObserver = class {constructor(){throw Error('unavailable')}}"
    )
    page.goto(base + "/history")
    wait_for_page(page)
    assert (
        page.locator(
            "#history-list [hidden], #history-list [inert], #history-list [aria-hidden=true]"
        ).count()
        == 0
    )
    for row in page.locator("#history-list > li").all():
        assert row.evaluate("node => getComputedStyle(node).opacity") == "1"
    page.locator("[data-report-select]").last.check()
    expect(page.locator("#history-delete-selected")).to_be_enabled()
    assert len(calls) == 1


def test_initial_failure_stops_and_retry_is_explicit(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    controls["fail_offset"] = 0
    page.goto(base + "/history")
    expect(page.locator("#history-retry")).to_be_visible()
    page.keyboard.press("End")
    page.wait_for_timeout(200)
    assert len(calls) == 1
    controls["fail_offset"] = None
    page.locator("#history-retry").click()
    wait_for_page(page)
    assert len(calls) == 2


def test_page_failure_preserves_complete_old_page_and_submitted_filters(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    page.goto(base + "/history")
    wait_for_page(page)
    controls["fail_offset"] = 24
    page.locator('#history-pagination [aria-label="Page 2"]').click()
    expect(page.locator("#history-retry")).to_be_visible()
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 1")
    expect(page.locator("#history-list a")).to_have_count(24)
    controls["fail_offset"] = None
    page.locator("#history-retry").click()
    wait_for_page(page)
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 25")
    assert calls[-1]["offset"] == ["24"]


def test_filter_no_matches_empty_and_unreadable_are_distinct(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    page.goto(base + "/history")
    wait_for_page(page)
    page.locator("#history-query").fill("no-such-report")
    page.get_by_role("button", name="Search reports", exact=True).click()
    expect(page.locator("#history-status")).to_contain_text("No reports match")
    expect(page.locator("#history-empty")).to_be_hidden()
    page.get_by_role("button", name="Clear filters", exact=True).click()
    wait_for_page(page)
    controls["unreadable_offset"] = 0
    page.get_by_role("button", name="Search reports", exact=True).click()
    expect(page.locator("#history-warnings")).to_be_visible()
    expect(page.locator("#history-list .status-warning")).to_be_visible()


def test_loading_blocks_duplicate_page_requests_and_selection(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    controls["hold_offset"] = 0
    page.goto(base + "/history")
    expect(page.locator("#history-scroll-stage")).to_have_attribute("data-phase", "loading")
    expect(page.locator("#history-select-all")).to_be_disabled()
    page.keyboard.press("End")
    page.mouse.wheel(0, 2000)
    page.wait_for_timeout(150)
    assert len(calls) == 1
    route, payload = controls["held_page"]
    controls["hold_offset"] = None
    route.fulfill(json=payload)
    wait_for_page(page)


def test_profile_colours_hover_and_complete_page_work_on_phone(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.set_viewport_size({"width": 320, "height": 844})
    page.goto(base + "/history")
    wait_for_page(page)
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
    links = page.locator("#history-list a")
    light = links.nth(0)
    deep = links.nth(1)
    normal = light.evaluate("node => getComputedStyle(node).color")
    deep_colour = deep.evaluate("node => getComputedStyle(node).color")
    assert normal != deep_colour
    light.hover()
    assert light.evaluate("node => getComputedStyle(node).color") == deep_colour
    # Scroll to the last record once; no further input is needed to expose it.
    links.last.scroll_into_view_if_needed()
    expect(links.last).to_contain_text("Saved report 24")
    assert len(calls) == 1
