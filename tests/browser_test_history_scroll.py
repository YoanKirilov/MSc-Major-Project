"""Progressive saved-report browsing, with synthetic API data and no device traffic."""

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
def history_browser(request, monkeypatch):
    from playwright.sync_api import sync_playwright

    listener = browser_listener()
    port = listener.getsockname()[1]
    monkeypatch.setenv("APP_PORT", str(port))
    manager = SessionManager()
    server = uvicorn.Server(uvicorn.Config(create_app(session_manager=manager), log_level="error"))
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
                    "title": f"Saved report {index + 1}",
                    "profile": ["light", "deep-tcp-v1", "unknown"][index % 3],
                    "state": "completed",
                    "created_at": "2026-10-12T10:00:00Z",
                    "device_count": 2,
                    "finding_count": 1,
                }
                for index in range(25)
            ]
            controls = {
                "fail_offset": None,
                "fail_query": None,
                "empty_offset": None,
                "report_count": 25,
            }

            def route_request(route):
                url = urlsplit(route.request.url)
                if url.hostname != "127.0.0.1" or route.request.method != "GET":
                    forbidden.append(route.request.url)
                    route.abort()
                    return
                if url.path == "/api/reports":
                    params = parse_qs(url.query)
                    calls.append(params)
                    offset = int(params.get("offset", [0])[0])
                    limit = int(params.get("limit", [1])[0])
                    assert limit == 1
                    query = params.get("q", [""])[0]
                    if controls["fail_offset"] == offset or controls["fail_query"] == query:
                        route.fulfill(status=503, json={"detail": "Synthetic local failure."})
                        return
                    matches = [
                        report
                        for report in reports[: controls["report_count"]]
                        if query.casefold() in report["title"].casefold()
                    ]
                    route.fulfill(
                        json={
                            "items": []
                            if controls["empty_offset"] == offset
                            else matches[offset : offset + limit],
                            "total": len(matches),
                            "warnings": [],
                            "unreadable_count": 0,
                        }
                    )
                    return
                route.continue_()

            context.route("**/*", route_request)
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            try:
                yield page, base, calls, controls
                assert not errors
                assert not forbidden
            finally:
                context.close()
                context = None
                browser.close()
                browser = None
    finally:
        if context is not None:
            context.close()
        if browser is not None:
            browser.close()
        server.should_exit = True
        thread.join(timeout=15)
        listener.close()


def test_zero_start_and_large_window_require_real_user_scroll(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.set_viewport_size({"width": 1280, "height": 2400})
    page.goto(base + "/history")
    expect(page.locator("#history-list a")).to_have_count(0)
    page.wait_for_timeout(150)
    assert len(calls) == 0
    page.locator("#history-query").focus()
    # Layout and programmatic scrolling must not fetch or reveal a first report.
    assert page.evaluate("document.documentElement.scrollHeight > innerHeight")
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(150)
    assert len(calls) == 0
    expect(page.locator("#history-list a")).to_have_count(0)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(50)
    page.mouse.move(640, 450)
    # Firefox caps an individual wheel gesture to about one viewport, even when
    # the injected delta is large. Use bounded real gestures until the list end.
    for _ in range(4):
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(150)
        if len(calls) > 0:
            break
    expect(page.locator("#history-list a")).to_have_count(1)
    expect(page.locator("#history-query")).to_be_focused()
    assert len(calls) == 1
    assert calls[0]["offset"] == ["0"]
    assert calls[0]["limit"] == ["1"]
    page.wait_for_timeout(450)
    assert len(calls) == 1
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(100)
    assert len(calls) == 1
    # A real downward wheel attempt at the absolute bottom has no scroll event.
    page.mouse.wheel(0, 500)
    expect(page.locator("#history-list a")).to_have_count(2)
    expect(page.locator("#history-query")).to_be_focused()
    assert len(calls) == 2


def test_keyboard_first_control_scrolls_before_loading_and_next_control_focuses_one_report(
    history_browser,
):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")
    expect(page.locator("#history-list a")).to_have_count(0)
    button = page.locator("#history-load-more")
    button.focus()
    page.wait_for_timeout(100)
    assert len(calls) == 0
    expect(button).to_have_text("Scroll to reports")
    button.press("Enter")
    expect(page.locator("#history-list a")).to_have_count(1)
    expect(page.locator("#history-list a").first).to_be_focused()
    assert page.evaluate("scrollY > 0")
    assert len(calls) == 1
    page.wait_for_timeout(450)
    assert len(calls) == 1
    button.focus()
    expect(button).to_have_text("Show next report")
    button.press("Enter")
    expect(page.locator("#history-list a")).to_have_count(2)
    expect(page.locator("#history-list a").nth(1)).to_be_focused()
    page.wait_for_timeout(450)
    assert len(calls) == 2


def test_append_failure_keeps_reports_and_retries_submitted_filters(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    page.goto(base + "/history")
    page.get_by_role("button", name="Scroll to reports", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(1)
    controls["fail_offset"] = 1
    page.locator("#history-query").fill("Unsubmitted query")
    page.locator("#history-load-more").click()
    expect(page.locator("#history-status")).to_contain_text("already shown are still available")
    expect(page.locator("#history-list a")).to_have_count(1)
    assert "q" not in calls[-1]
    controls["fail_offset"] = None
    page.get_by_role("button", name="Retry loading reports", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(2)
    assert calls[-1]["offset"] == ["1"]
    assert "q" not in calls[-1]


def test_filter_reset_waits_for_fresh_scroll_and_failed_reveal_retry_focuses_first_report(
    history_browser,
):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    page.goto(base + "/history")
    page.get_by_role("button", name="Scroll to reports", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(1)
    controls["fail_query"] = "Saved report 25"
    page.locator("#history-query").fill("Saved report 25")
    page.get_by_role("button", name="Search reports", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(0)
    expect(page.locator("#history-status")).to_contain_text("Filters are ready")
    page.wait_for_timeout(150)
    assert len(calls) == 1
    page.get_by_role("button", name="Scroll to reports", exact=True).click()
    expect(page.locator("#history-status")).to_contain_text("Synthetic local failure")
    expect(page.locator("#history-list a")).to_have_count(0)
    controls["fail_query"] = None
    page.get_by_role("button", name="Retry loading reports", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(1)
    expect(page.locator("#history-list a")).to_be_focused()
    expect(page.locator("#history-status")).to_contain_text("Showing 1 of 1 reports")
    expect(page.locator("#history-load-more")).to_be_disabled()
    assert calls[-1]["offset"] == ["0"]
    page.get_by_role("button", name="Clear filters", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(0)
    previous_calls = len(calls)
    page.wait_for_timeout(150)
    assert len(calls) == previous_calls
    page.get_by_role("button", name="Scroll to reports", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(1)
    assert "q" not in calls[-1]


def test_mobile_one_at_a_time_reaches_the_end_without_overflow_or_hidden_links(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    controls["report_count"] = 3
    page.set_viewport_size({"width": 320, "height": 844})
    page.goto(base + "/history")
    expect(page.locator("#history-list a")).to_have_count(0)
    for count in (1, 2, 3):
        button = page.locator("#history-load-more")
        button.focus()
        button.press("Enter")
        expect(page.locator("#history-list a")).to_have_count(count)
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    expect(page.locator("#history-load-more")).to_be_disabled()
    expect(page.locator("#history-more-hint")).to_contain_text("reached the end")
    assert len(calls) == 3
    assert page.locator("#history-list a").evaluate_all(
        "links => links.every(link => getComputedStyle(link).visibility === 'visible')"
    )


def test_changed_history_offers_refresh_without_claiming_all_reports_are_shown(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    page.goto(base + "/history")
    page.get_by_role("button", name="Scroll to reports", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(1)
    controls["empty_offset"] = 1
    page.locator("#history-load-more").click()
    expect(page.locator("#history-warnings")).to_contain_text("changed while you were browsing")
    expect(page.locator("#history-list a")).to_have_count(1)
    refresh = page.get_by_role("button", name="Refresh reports", exact=True)
    expect(refresh).to_be_enabled()
    expect(page.locator("#history-more-hint")).to_contain_text("check for missing or new reports")
    page.locator("#history-query").fill("Unsubmitted query")
    refresh.click()
    expect(page.locator("#history-list a")).to_have_count(0)
    previous_calls = len(calls)
    page.wait_for_timeout(150)
    assert len(calls) == previous_calls
    page.get_by_role("button", name="Scroll to reports", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(1)
    expect(page.locator("#history-list a").first).to_be_focused()
    assert calls[-1]["offset"] == ["0"]
    assert "q" not in calls[-1]


def test_wheel_burst_is_one_gesture_and_profile_markers_are_semantic(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")
    page.get_by_role("button", name="Scroll to reports", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(1)
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.mouse.move(640, 450)
    for _ in range(5):
        page.mouse.wheel(0, 400)
        page.wait_for_timeout(20)
    expect(page.locator("#history-list a")).to_have_count(2)
    page.wait_for_timeout(450)
    assert len(calls) == 2
    page.mouse.wheel(0, 400)
    expect(page.locator("#history-list a")).to_have_count(3)
    assert len(calls) == 3
    assert page.locator("#history-list a").evaluate_all(
        "links => links.map(link => link.dataset.profile)"
    ) == ["light", "deep-tcp-v1", "unknown"]


def test_held_scroll_key_does_not_reveal_multiple_reports(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")
    page.locator("#history-load-more").focus()
    assert len(calls) == 0
    page.keyboard.down("PageDown")
    expect(page.locator("#history-list a")).to_have_count(1)
    for _ in range(3):
        page.keyboard.down("PageDown")
    page.wait_for_timeout(450)
    expect(page.locator("#history-list a")).to_have_count(1)
    assert len(calls) == 1
    page.keyboard.up("PageDown")
    page.keyboard.press("End")
    expect(page.locator("#history-list a")).to_have_count(2)
    assert len(calls) == 2


def test_touch_contact_alone_is_inert_and_each_downward_swipe_reveals_one(history_browser):
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

    # This exercises gesture wiring with synthetic events, not physical touch hardware.
    touch("touchstart", 300)
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(100)
    expect(page.locator("#history-list a")).to_have_count(0)
    assert len(calls) == 0
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
    assert len(calls) == 1
    touch("touchstart", 300)
    touch("touchmove", 200)
    expect(page.locator("#history-list a")).to_have_count(2)
    assert len(calls) == 2


@pytest.mark.parametrize("outcome", ["empty", "no_match", "error"])
def test_big_wheel_with_no_report_keeps_feedback_on_screen_without_focus_theft(
    history_browser, outcome
):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    if outcome == "empty":
        controls["report_count"] = 0
    elif outcome == "error":
        controls["fail_offset"] = 0
    page.goto(base + "/history")
    expect(page.locator("#history-list a")).to_have_count(0)
    assert len(calls) == 0
    if outcome == "no_match":
        page.locator("#history-query").fill("A report that does not exist")
        page.get_by_role("button", name="Search reports", exact=True).click()
        expect(page.locator("#history-status")).to_contain_text("Filters are ready")
        assert len(calls) == 0
    query = page.locator("#history-query")
    query.focus()
    page.mouse.move(640, 450)
    # A browser may cap each wheel input to one viewport. Never require an extra
    # request: bounded gestures stop as soon as the first requested result exists.
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
    expect(page.locator("#history-scroll-stage")).to_have_attribute("data-has-more", "false")
