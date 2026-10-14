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


def wait_for_scroll_frame(page):
    """Native keyboard default actions require a painted scrollable frame."""
    # Navigation's load event can precede the first painted scrollable frame.
    # Native keys require that frame; never substitute a programmatic scroll.
    page.evaluate(
        "() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))"
    )


def reveal_with_keyboard(page, expected_count=None):
    """Use an ordinary native scrolling key, never programmatic loading."""
    from playwright.sync_api import expect

    page.locator("#history-status").focus()
    wait_for_scroll_frame(page)
    page.keyboard.press("End")
    if expected_count is not None:
        try:
            expect(page.locator("#history-list > li")).to_have_count(expected_count)
        except AssertionError as exc:
            state = page.evaluate(
                """() => {
                    const bounds = id => document.querySelector(`#history-${id}`)
                        .getBoundingClientRect().toJSON();
                    return ({
                    ready: document.readyState,
                    hasFocus: document.hasFocus(),
                    dialogs: [...document.querySelectorAll('dialog')].map(dialog =>
                        ({id: dialog.id, open: dialog.open})),
                    scrollY, height: innerHeight,
                    documentHeight: document.documentElement.scrollHeight,
                    phase: document.querySelector('#history-scroll-stage').dataset.phase,
                    status: document.querySelector('#history-status').textContent,
                    stage: bounds('scroll-stage'),
                    sentinel: bounds('sentinel'),
                    focused: document.activeElement?.id,
                    count: document.querySelectorAll('#history-list > li').length
                }); }"""
            )
            raise AssertionError(
                f"Expected {expected_count} report rows; history state: {state}"
            ) from exc


def test_zero_start_and_large_window_require_real_user_scroll(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.set_viewport_size({"width": 1280, "height": 2400})
    page.goto(base + "/history")
    expect(page.locator("#history-list a")).to_have_count(0)
    page.wait_for_timeout(150)
    assert not calls
    page.locator("#history-query").focus()
    assert page.evaluate("document.documentElement.scrollHeight > innerHeight")
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(150)
    assert not calls
    expect(page.locator("#history-list a")).to_have_count(0)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(50)
    page.mouse.move(640, 450)
    for _ in range(4):
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(150)
        if calls:
            break
    expect(page.locator("#history-list a")).to_have_count(1)
    expect(page.locator("#history-query")).to_be_focused()
    assert len(calls) == 1
    assert calls[0]["offset"] == ["0"]
    assert calls[0]["limit"] == ["24"]
    page.wait_for_timeout(450)
    assert len(calls) == 1
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(100)
    expect(page.locator("#history-list a")).to_have_count(1)
    page.mouse.wheel(0, 500)
    expect(page.locator("#history-list a")).to_have_count(2)
    expect(page.locator("#history-query")).to_be_focused()
    assert len(calls) == 1  # Further rows are revealed from the bounded cached page.


def test_native_keyboard_scroll_reveals_rows_without_next_report_buttons(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")
    expect(page.locator("#history-list a")).to_have_count(0)
    assert not calls
    assert page.locator("#history-load-more, #history-load-more-end").count() == 0
    reveal_with_keyboard(page, 1)
    expect(page.locator("#history-status")).to_be_focused()
    assert page.evaluate("scrollY > 0")
    assert len(calls) == 1
    page.wait_for_timeout(100)
    reveal_with_keyboard(page, 2)
    expect(page.locator("#history-status")).to_be_focused()
    expect(page.locator("#history-list a").nth(1)).to_contain_text("Saved report 2")
    assert len(calls) == 1


def test_page_failure_keeps_reports_and_retries_submitted_filters(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    controls["fail_offset"] = 24
    page.locator("#history-query").fill("Unsubmitted query")
    page.locator('#history-pagination [data-page="2"]').first.click()
    expect(page.locator("#history-status")).to_contain_text("already")
    expect(page.locator("#history-list a")).to_have_count(1)
    expect(page.locator("#history-list a")).to_contain_text("Saved report 1")
    expect(page.locator("#history-retry")).to_be_visible()
    assert "q" not in calls[-1]
    controls["fail_offset"] = None
    page.locator("#history-retry").click()
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 25")
    assert calls[-1]["offset"] == ["24"]
    assert "q" not in calls[-1]


def test_filter_reset_waits_for_fresh_scroll_and_failed_reveal_is_retryable(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    controls["fail_query"] = "Saved report 53"
    page.locator("#history-query").fill("Saved report 53")
    page.get_by_role("button", name="Search reports", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(0)
    expect(page.locator("#history-status")).to_contain_text("Filters are ready")
    page.wait_for_timeout(150)
    assert len(calls) == 1
    reveal_with_keyboard(page)
    expect(page.locator("#history-status")).to_contain_text("Synthetic local failure")
    expect(page.locator("#history-list a")).to_have_count(0)
    controls["fail_query"] = None
    page.locator("#history-retry").click()
    expect(page.locator("#history-list a")).to_have_count(1)
    expect(page.locator("#history-list a")).to_contain_text("Saved report 53")
    assert calls[-1]["offset"] == ["0"]
    page.get_by_role("button", name="Clear filters", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(0)
    previous_calls = len(calls)
    page.wait_for_timeout(150)
    assert len(calls) == previous_calls
    reveal_with_keyboard(page, 1)
    assert "q" not in calls[-1]


def test_mobile_one_at_a_time_reaches_the_end_without_overflow(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    controls["report_count"] = 3
    page.set_viewport_size({"width": 320, "height": 844})
    page.goto(base + "/history")
    expect(page.locator("#history-list a")).to_have_count(0)
    for count in (1, 2, 3):
        reveal_with_keyboard(page, count)
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    expect(page.locator("#history-status")).to_contain_text("3")
    assert len(calls) == 1
    assert page.locator("#history-list a").evaluate_all(
        "links => links.every(link => getComputedStyle(link).visibility === 'visible')"
    )
    reveal_with_keyboard(page, 3)
    assert len(calls) == 1


def test_changed_history_offers_refresh_without_duplicate_reports(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    controls["duplicate_offset"] = 0
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    expect(page.locator("#history-warnings")).to_contain_text("changed while you were browsing")
    expect(page.locator("#history-refresh")).to_be_visible()
    page.locator("#history-query").fill("Unsubmitted query")
    page.locator("#history-refresh").click()
    expect(page.locator("#history-list a")).to_have_count(0)
    previous_calls = len(calls)
    page.wait_for_timeout(150)
    assert len(calls) == previous_calls
    controls["duplicate_offset"] = None
    reveal_with_keyboard(page, 1)
    assert calls[-1]["offset"] == ["0"]
    assert "q" not in calls[-1]


def test_wheel_burst_is_one_gesture_and_profile_markers_remain_semantic(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.mouse.move(640, 450)
    for _ in range(5):
        page.mouse.wheel(0, 400)
        page.wait_for_timeout(20)
    expect(page.locator("#history-list a")).to_have_count(2)
    page.wait_for_timeout(450)
    page.mouse.wheel(0, 400)
    expect(page.locator("#history-list a")).to_have_count(3)
    assert len(calls) == 1
    assert page.locator("#history-list a").evaluate_all(
        "links => links.map(link => link.dataset.profile)"
    ) == ["light", "deep-tcp-v1", "unknown"]


def test_held_scroll_key_does_not_reveal_multiple_reports(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")
    page.locator("#history-status").focus()
    wait_for_scroll_frame(page)
    assert not calls
    page.keyboard.down("End")
    expect(page.locator("#history-list a")).to_have_count(1)
    for _ in range(3):
        page.keyboard.down("End")
    page.wait_for_timeout(450)
    expect(page.locator("#history-list a")).to_have_count(1)
    assert len(calls) == 1
    page.keyboard.up("End")
    page.keyboard.press("End")
    expect(page.locator("#history-list a")).to_have_count(2)
    assert len(calls) == 1


def test_touch_contact_is_inert_and_each_downward_swipe_reveals_one(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")

    def touch(name, y):
        page.evaluate(
            """([name, y]) => {
                const event = new Event(name);
                Object.defineProperty(event, 'touches', { value: [{ clientY: y }] });
                window.dispatchEvent(event);
            }""",
            [name, y],
        )

    # Synthetic event wiring is not a claim of physical touch-device verification.
    touch("touchstart", 300)
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(100)
    expect(page.locator("#history-list a")).to_have_count(0)
    assert not calls
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(50)
    touch("touchstart", 300)
    touch("touchmove", 200)
    page.evaluate("window.scrollBy(0, 250)")
    expect(page.locator("#history-list a")).to_have_count(1)
    touch("touchmove", 100)
    page.evaluate("window.scrollBy(0, 250)")
    page.wait_for_timeout(100)
    expect(page.locator("#history-list a")).to_have_count(1)
    touch("touchstart", 300)
    touch("touchmove", 200)
    expect(page.locator("#history-list a")).to_have_count(2)
    assert len(calls) == 1


@pytest.mark.parametrize("outcome", ["empty", "no_match", "error"])
def test_big_wheel_without_reports_keeps_feedback_visible_without_focus_theft(
    history_browser, outcome
):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    if outcome == "empty":
        controls["report_count"] = 0
    elif outcome == "error":
        controls["fail_offset"] = 0
    page.goto(base + "/history")
    if outcome == "no_match":
        page.locator("#history-query").fill("A report that does not exist")
        page.get_by_role("button", name="Search reports", exact=True).click()
        expect(page.locator("#history-status")).to_contain_text("Filters are ready")
    assert not calls
    query = page.locator("#history-query")
    query.focus()
    page.mouse.move(640, 450)
    for _ in range(4):
        page.mouse.wheel(0, 5000)
        page.wait_for_timeout(150)
        if calls:
            break
    if outcome == "empty":
        feedback = page.locator("#history-empty")
        expect(feedback).to_contain_text("No saved reports yet")
    else:
        feedback = page.locator("#history-status")
        expect(feedback).to_contain_text(
            "No reports match your filters" if outcome == "no_match" else "Synthetic local failure"
        )
    page.wait_for_timeout(450)
    bounds = feedback.bounding_box()
    assert bounds is not None
    assert bounds["y"] >= -1, bounds
    assert bounds["y"] + bounds["height"] <= page.viewport_size["height"] + 1, bounds
    expect(query).to_be_focused()
    expect(page.locator("#history-list a")).to_have_count(0)
    assert len(calls) == 1
    expect(page.locator("#history-scroll-stage")).to_have_attribute(
        "data-phase", "error" if outcome == "error" else "ready"
    )


def test_initial_page_loading_blocks_duplicate_scroll_requests(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    controls["hold_offset"] = 0
    page.goto(base + "/history")
    reveal_with_keyboard(page)
    expect(page.locator("#history-list")).to_have_attribute("aria-busy", "true")
    expect(page.locator("#history-list a")).to_have_count(0)
    for _ in range(3):
        page.keyboard.press("End")
    page.wait_for_timeout(150)
    assert len(calls) == 1
    route, payload = controls["held_page"]
    controls["hold_offset"] = None
    route.fulfill(json=payload)
    expect(page.locator("#history-list a")).to_have_count(1)
    expect(page.locator("#history-status")).to_be_focused()
    assert page.locator("#history-list").get_attribute("aria-busy") is None
    assert len(calls) == 1


def test_unreadable_report_keeps_focus_and_does_not_offer_deletion(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    controls["unreadable_offset"] = 0
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    warning = page.locator("#history-list > li").first
    expect(warning).to_contain_text("could not be read")
    expect(page.locator("#history-status")).to_be_focused()
    expect(page.locator("#history-list a")).to_have_count(0)
    assert warning.locator("[data-report-select], [data-report-delete]").count() == 0
    reveal_with_keyboard(page, 2)
    expect(page.locator("#history-list a")).to_have_count(1)
    expect(page.locator("#history-list a")).to_contain_text("Saved report 2")
    assert len(calls) == 1
