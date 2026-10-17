"""Offline reproduction and regression gates for the 14 October UX changes."""

import os

import pytest
from tests import browser_test_history_scroll as history_cases
from tests.browser_test_ui_ux import ui as _report_ui
from tests.fixtures.browser import assert_page_reflows, wait_for_report_ready

history_browser = history_cases.history_browser
ui = _report_ui
wait_for_page = history_cases.wait_for_page
pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browser"),
]


def test_history_distinct_controls_context_and_recovery_survive_reload(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    controls["reports"][0]["title"] = controls["reports"][1]["title"] = "Same title"
    page.goto(base + "/history")
    wait_for_page(page)
    names = page.locator("[data-report-select]").evaluate_all(
        "nodes => nodes.map(node => node.getAttribute('aria-label'))"
    )
    assert names[0] != names[1]
    page.locator("[data-report-delete]").first.click()
    expect(page.locator("#history-delete-list")).to_contain_text(controls["reports"][0]["scan_id"])
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-feedback")).to_contain_text("1 report deleted")
    page.reload()
    wait_for_page(page)
    expect(page.locator("#history-undo-delete")).to_be_hidden()
    count = len(calls)
    page.wait_for_timeout(100)
    assert len(calls) == count
    page.locator("#recovery-copies summary").click()
    page.locator("#recovery-load").click()
    expect(page.locator("#recovery-list li")).to_have_count(1)
    page.locator("#recovery-list button").click()
    expect(page.locator("#recovery-status")).to_contain_text("notes restored")
    assert not controls["deleted"]
    wait_for_page(page)
    page.locator('#history-pagination [data-page="2"]').first.click()
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 25")
    page.locator("[data-report-select]").first.check()
    page.reload()
    wait_for_page(page)
    expect(page.locator("#history-delete-selected")).to_be_disabled()
    expect(page.locator("#history-status")).to_contain_text("Page 2 of 3")
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 25")
    assert calls[-1]["offset"] == ["24"]


def test_old_backend_storage_shape_explains_restart_instead_of_nan(history_browser):
    from playwright.sync_api import expect

    page, base, _, _ = history_browser
    page.route(
        "**/api/storage-usage", lambda route: route.fulfill(json={"bytes": 1048576, "files": 2})
    )
    page.route(
        "**/api/report-capabilities",
        lambda route: route.fulfill(status=404, json={"detail": "Not Found"}),
    )
    page.goto(base + "/history")
    expect(page.locator("#history-backend-status")).to_contain_text("Restart")
    page.locator("details").filter(has=page.locator("#storageUsageButton")).locator(
        "summary"
    ).click()
    page.locator("#storageUsageButton").click()
    expect(page.locator("#storageUsage")).to_contain_text("older active-data measurement")
    expect(page.locator("#storageUsage")).not_to_contain_text("NaN")
    expect(page.locator("#storageUsage")).to_contain_text("Recovery copies are not included")


def test_running_actions_keep_focus_and_pending_cancellation_across_changed_polls(ui):
    from playwright.sync_api import expect

    page, base, _ = ui
    item = {
        "scan_id": "11111111-1111-4111-8111-111111111111",
        "profile": "light",
        "target": {"hosts": ["192.168.56.10"]},
        "phase": "service_scan",
        "completed": 0,
        "total": 5,
    }
    jobs = [item]
    writes = []
    page.route("**/api/running-scans", lambda route: route.fulfill(json={"items": jobs}))
    page.route(
        "**/api/live-scans/" + item["scan_id"],
        lambda route: (writes.append(route.request.method), route.fulfill(json={"ok": True})),
    )
    page.goto(base + "/")
    actions = page.locator("#runningScans .running-scan-actions")
    expect(actions).to_be_visible()
    for index in range(3):
        control = actions.locator("a, button").nth(index)
        control.evaluate("node => { window.focusedJobAction = node; node.focus(); }")
        item["completed"] += 1
        expect(page.locator("#runningScans article > p").first).to_contain_text(
            f"{item['completed']} of 5", timeout=6500
        )
        assert page.evaluate(
            "window.focusedJobAction === document.activeElement "
            "&& window.focusedJobAction.isConnected"
        )
    page.once("dialog", lambda dialog: dialog.accept())
    actions.locator("button").click()
    expect(actions.locator("button")).to_have_text("Cancellation requested")
    item["completed"] += 1
    expect(page.locator("#runningScans article > p").first).to_contain_text("4 of 5", timeout=6500)
    expect(actions.locator("button")).to_be_disabled()
    assert writes == ["DELETE"]
    actions.locator("a").first.focus()
    jobs.clear()
    expect(page.locator("#runningScansNote")).to_be_focused(timeout=6500)
    expect(page.locator("#runningScansNote")).to_contain_text("no longer running")


def test_settings_durable_save_dirty_discard_and_instant_preferences(ui):
    from playwright.sync_api import expect

    page, base, _ = ui
    writes = []

    def save(route):
        writes.append(route.request.post_data_json)
        route.fulfill(json={**writes[-1], "revision": writes[-1]["expected_revision"] + 1})

    page.route(
        "**/api/settings",
        lambda route: save(route) if route.request.method == "PATCH" else route.continue_(),
    )
    page.goto(base + "/settings")
    expect(page.locator("#save-settings")).to_be_enabled()
    page.locator("#themePreference").select_option("light")
    expect(page.locator("#appearance-feedback")).to_contain_text("applied and remembered")
    expect(page.locator("#discard-settings")).to_be_hidden()
    page.locator("#scope-mode").select_option("manual")
    page.locator("#allowed-network").fill("192.168.56.0/24")
    expect(page.locator("#settings-status")).to_contain_text("Unsaved")
    page.locator("#save-settings").click()
    expect(page.locator("#settings-status")).to_contain_text("settings saved")
    assert page.url.endswith("/settings")
    expect(page.locator("#discard-settings")).to_be_hidden()
    page.locator("#allowed-network").fill("192.168.57.0/24")
    expect(page.locator("#discard-settings")).to_be_visible()
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.locator("#discard-settings").click()
    expect(page.locator("#allowed-network")).to_have_value("192.168.57.0/24")
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#discard-settings").click()
    expect(page.locator("#discard-settings")).to_be_hidden()
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    assert len(writes) == 1


def test_report_wording_source_keyboard_path_and_small_screen_text_spacing(ui):
    from playwright.sync_api import expect

    page, base, reports = ui
    spacing = (
        "* {line-height: 1.5 !important; letter-spacing: .12em !important; "
        "word-spacing: .16em !important} p {margin-bottom: 2em !important}"
    )
    page.route(
        "**/static/css/ux-report-spacing.css",
        lambda route: route.fulfill(content_type="text/css", body=spacing),
    )
    page.emulate_media(forced_colors="active")
    page.set_viewport_size({"width": 320, "height": 900})
    page.goto(base + "/scans/" + reports["rich"].scan_id)
    wait_for_report_ready(page)
    page.add_style_tag(url=base + "/static/css/ux-report-spacing.css")
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
    source = page.locator("#detailPanel .wording-provenance")
    expect(source).to_be_visible()
    expect(source).to_contain_text("about this wording")
    source.focus()
    page.keyboard.press("Enter")
    details = page.locator("#detailPanel > .supporting-details")
    expect(details).to_have_attribute("open", "")
    expect(details.locator("summary").first).to_be_focused()
    expect(details).to_contain_text("not an independent test")


def test_theme_forced_colours_and_text_spacing_reflow_without_scan_requests(history_browser):
    from playwright.sync_api import expect

    page, base, _, _ = history_browser
    page.route(
        "**/api/status",
        lambda route: route.fulfill(
            json={
                "scanner_available": True,
                "ui_contract_version": 1,
                "allowed_network": "192.168.56.0/24",
                "detected_network": "192.168.56.0/24",
                "scope_source": "automatic",
                "storage_available": True,
                "scan_slots_available": True,
                "interface_choices": [],
                "mdns_available": False,
            }
        ),
    )
    page.route("**/api/running-scans", lambda route: route.fulfill(json={"items": []}))
    page.route("**/api/recent-devices", lambda route: route.fulfill(json={"items": []}))
    spacing = (
        "html {font-size: 200% !important} * {line-height: 1.5 !important; "
        "letter-spacing: .12em !important; word-spacing: .16em !important} "
        "p {margin-bottom: 2em !important}"
    )
    page.route(
        "**/static/css/ux-test-spacing.css",
        lambda route: route.fulfill(content_type="text/css", body=spacing),
    )
    page.emulate_media(color_scheme="light", forced_colors="active")
    page.goto(base + "/settings")
    page.locator("#themePreference").select_option("system")
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    page.emulate_media(color_scheme="dark", forced_colors="active")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.locator("#themePreference").select_option("light")
    page.emulate_media(color_scheme="dark", forced_colors="active")
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    for path in ("/settings", "/history", "/"):
        page.goto(base + path)
        page.set_viewport_size({"width": 320, "height": 900})
        page.add_style_tag(url=base + "/static/css/ux-test-spacing.css")
        assert_page_reflows(page, f"Forced colours and 200% text spacing: {path}")
        link = page.locator(".skip-link")
        link.focus()
        assert link.evaluate("node => getComputedStyle(node).outlineStyle !== 'none'")
