"""Exact saved-device reading context and save feedback; synthetic evidence only."""

import os
from urllib.parse import urlencode

import pytest
from tests.browser_test_ui_ux import _open
from tests.browser_test_ui_ux import ui as ui

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browsers"),
]


def _ready(page):
    from playwright.sync_api import expect

    # Navigation's load event does not wait for the report/session GETs. Settle
    # those reads before asserting restored state, as on other browser pages.
    page.wait_for_load_state("networkidle")
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")


def _watch_messages(page):
    page.evaluate("""() => {
        const region = document.querySelector('#report-interaction-status');
        region.textContent = '';
        window.reportMessages = [];
        new MutationObserver(() => {
            if (region.textContent.trim()) window.reportMessages.push(region.textContent.trim());
        }).observe(region, {childList:true, subtree:true, characterData:true});
    }""")


@pytest.mark.parametrize("width", [320, 1440])
def test_explicit_device_context_reveals_exact_card_without_hiding_facts_or_resetting_other_filters(
    ui, width
):
    from playwright.sync_api import expect

    page, report = _open(ui, size=(width, 900))
    page.locator("#deviceSearchInput").fill("not a matching device")
    page.locator("#deviceSort").select_option("name")
    page.locator("#checklist-filter").select_option("need_help")
    target = report.devices[2]
    page.goto(
        ui[1]
        + f"/scans/{report.scan_id}?"
        + urlencode({"device": target.device_id})
        + "#devices-title"
    )
    _ready(page)
    selected = page.locator(".device-context-highlight")
    expect(selected).to_have_count(1)
    expect(selected).to_have_attribute("data-device-id", target.device_id)
    expect(selected.locator(".device-summary")).to_have_attribute("open", "")
    expect(selected.locator(".device-summary > summary")).to_be_focused()
    expect(page.locator("#deviceSearchInput")).to_have_value("")
    expect(page.locator("#deviceSort")).to_have_value("name")
    expect(page.locator("#checklist-filter")).to_have_value("need_help")
    expect(page.locator(".device-summary-group")).to_have_count(4)
    expect(page.locator("#report-device-context-status")).to_contain_text("All other devices")
    assert page.locator("#report-device-context-status").get_attribute("role") == "status"
    assert selected.bounding_box()["y"] >= 0
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")


def test_late_device_context_expands_only_the_needed_saved_device_page(ui):
    from playwright.sync_api import expect

    page, report = _open(ui, kind="many", size=(1440, 1000))
    expect(page.locator(".device-summary-group")).to_have_count(24)
    target = report.devices[90]
    page.goto(
        ui[1]
        + f"/scans/{report.scan_id}?"
        + urlencode({"device": target.device_id})
        + "#devices-title"
    )
    _ready(page)
    expect(page.locator(".device-context-highlight")).to_have_attribute(
        "data-device-id", target.device_id
    )
    expect(page.locator(".device-summary-group")).to_have_count(96)
    expect(page.locator("#showMoreDevices")).to_contain_text("4 remaining")
    expect(page.locator("#device-search-count")).to_contain_text("100 recorded in total")


def test_reload_and_back_restore_later_reading_state_after_explicit_device_link(ui):
    from playwright.sync_api import expect

    page, report = _open(ui, size=(768, 1024))
    target = report.devices[2]
    page.goto(
        ui[1]
        + f"/scans/{report.scan_id}?"
        + urlencode({"device": target.device_id})
        + "#devices-title"
    )
    _ready(page)
    page.locator("#deviceSearchInput").fill(report.devices[0].ip)
    page.locator("#deviceSort").select_option("address")
    page.locator("#next-title").evaluate("node => node.scrollIntoView({block:'start'})")
    key = "netguard-report-view-v1:" + report.scan_id
    page.wait_for_function(
        """key => {
        const value = JSON.parse(sessionStorage.getItem(key) || '{}');
        return value.contextDeviceId && value.devices && Math.abs(value.y - scrollY) < 3;
    }""",
        arg=key,
    )
    before = page.evaluate("scrollY")
    page.reload()
    _ready(page)
    expect(page.locator("#deviceSearchInput")).to_have_value(report.devices[0].ip)
    expect(page.locator(".device-context-highlight")).to_have_count(0)
    expect(page.locator("#report-device-context-status")).to_contain_text("not in this view")
    page.wait_for_function("value => Math.abs(scrollY - value) < 5", arg=before)
    page.goto(ui[1] + "/devices")
    page.go_back()
    _ready(page)
    expect(page.locator("#deviceSearchInput")).to_have_value(report.devices[0].ip)
    expect(page.locator(".device-context-highlight")).to_have_count(0)


@pytest.mark.parametrize(
    "query", ["device=missing", "device=one&device=two", "device=%E2%80%AEbad"]
)
def test_missing_or_invalid_device_context_preserves_saved_view_and_selects_no_substitute(
    ui, query
):
    from playwright.sync_api import expect

    page, report = _open(ui)
    page.locator("#deviceSearchInput").fill(report.devices[0].ip)
    page.locator("#deviceSort").select_option("address")
    page.goto(ui[1] + f"/scans/{report.scan_id}?{query}#devices-title")
    _ready(page)
    expect(page.locator("#deviceSearchInput")).to_have_value(report.devices[0].ip)
    expect(page.locator("#deviceSort")).to_have_value("address")
    expect(page.locator(".device-context-highlight")).to_have_count(0)
    expect(page.locator("#report-device-context-status")).to_contain_text("No other device")
    assert page.locator("#report-device-context-status").get_attribute("role") != "alert"


def test_checklist_outcome_has_one_live_region_while_visible_row_feedback_remains(ui):
    from playwright.sync_api import expect

    page, _ = _open(ui)
    _watch_messages(page)
    checklist = page.locator("#nextStepsList .next-step-checklist").first
    checklist.locator(":scope > summary").click()
    row = checklist.locator(".action-check").first
    row.locator("select").select_option("checked")
    expect(row.locator(".action-check-note")).to_contain_text("Checklist saved")
    expect(page.locator("#report-interaction-status")).to_contain_text("Checklist saved")
    assert len(page.evaluate("window.reportMessages")) == 1
    assert row.locator(".action-check-note").get_attribute("role") is None
    for selector in ("#checklist-notice", "#checklist-progress", "#checklist-filter-count"):
        assert page.locator(selector).get_attribute("role") is None


def test_uncertain_checklist_write_keeps_choice_and_needs_explicit_retry(ui):
    from playwright.sync_api import expect

    page, report = _open(ui)
    writes = []
    endpoint = f"**/api/live-scans/{report.scan_id}/action-checks"

    def fail(route):
        writes.append(route.request.post_data_json)
        route.fulfill(status=503, content_type="application/json", body='{"detail":"Test delay"}')

    page.route(endpoint, fail)
    _watch_messages(page)
    checklist = page.locator("#nextStepsList .next-step-checklist").first
    checklist.locator(":scope > summary").click()
    row = checklist.locator(".action-check").first
    row.locator("select").select_option("checked")
    expect(row.locator(".action-check-note")).to_contain_text("could not be confirmed")
    expect(row.locator(".action-check-note")).to_contain_text("kept here as a draft")
    expect(row.locator("select")).to_have_value("checked")
    expect(page.locator("#checklist-progress")).to_contain_text("0 of")
    expect(row.get_by_role("button", name="Save this choice", exact=True)).to_be_visible()
    assert len(writes) == 1
    assert len(page.evaluate("window.reportMessages")) == 1
    page.unroute(endpoint)
    row.get_by_role("button", name="Save this choice", exact=True).click()
    expect(row.locator(".action-check-note")).to_contain_text("Checklist saved")
    expect(row.get_by_role("button", name="Save this choice", exact=True)).to_be_hidden()
    assert len(page.evaluate("window.reportMessages")) == 2


def test_nickname_success_announces_after_close_and_failure_stays_local_with_draft(ui):
    from playwright.sync_api import expect

    page, report = _open(ui)
    _watch_messages(page)
    trigger = page.locator("[data-nickname-device]").first
    trigger.click()
    page.locator("#annotationEditorInput").fill("My saved device")
    page.locator("#annotationEditorSave").click()
    expect(page.locator("#annotationEditorDialog")).not_to_be_visible()
    expect(page.locator("#report-interaction-status")).to_contain_text("nickname was saved")
    assert len(page.evaluate("window.reportMessages")) == 1
    expect(page.locator("[data-nickname-status]").first).to_contain_text("nickname was saved")
    assert page.locator("[data-nickname-status]").first.get_attribute("role") is None
    writes = []
    endpoint = f"**/api/live-scans/{report.scan_id}/devices/*/nickname"

    def fail(route):
        writes.append(route.request.post_data_json)
        route.fulfill(status=503, content_type="application/json", body='{"detail":"Test delay"}')

    page.route(endpoint, fail)
    trigger.click()
    page.locator("#annotationEditorInput").fill("Keep this draft")
    page.locator("#annotationEditorSave").click()
    expect(page.locator("#annotationEditorStatus")).to_contain_text("could not be confirmed")
    expect(page.locator("#annotationEditorInput")).to_have_value("Keep this draft")
    expect(page.locator("#annotationEditorDialog")).to_be_visible()
    assert page.locator("#annotationEditorStatus").get_attribute("role") == "status"
    assert len(writes) == 1
    assert len(page.evaluate("window.reportMessages")) == 1
