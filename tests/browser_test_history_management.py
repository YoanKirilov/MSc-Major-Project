"""Full bounded pages and confirmed deletion, with synthetic data only."""

import os

import pytest
from tests import browser_test_history_scroll as history_cases

history_browser = history_cases.history_browser
wait_for_page = history_cases.wait_for_page
pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browser"),
]


def test_pages_cap_at_24_and_explicit_navigation_replaces_page(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")
    wait_for_page(page)
    page.locator('#history-pagination [aria-label="Page 2"]').click()
    wait_for_page(page)
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 25")
    expect(page.locator("#history-list a").last).to_contain_text("Saved report 48")
    assert "Page 2 of 3" in page.title()
    page.locator('#history-pagination [aria-label="Page 3"]').click()
    wait_for_page(page, 5)
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 49")
    assert [item["offset"] for item in calls] == [["0"], ["24"], ["48"]]
    page.keyboard.press("End")
    page.wait_for_timeout(100)
    assert len(calls) == 3


def test_filters_load_immediately_reset_page_and_clear_selection(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")
    wait_for_page(page)
    page.locator('#history-pagination [aria-label="Page 2"]').click()
    wait_for_page(page)
    page.locator("[data-report-select]").first.check()
    page.locator("#history-profile").select_option("deep-tcp-v1")
    page.get_by_role("button", name="Search reports", exact=True).click()
    wait_for_page(page, 18)
    expect(page.locator("[data-report-select]:checked")).to_have_count(0)
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 2")
    expect(page.locator("#history-applied-filters")).to_have_text("Type: Deep")
    assert calls[-1]["offset"] == ["0"] and calls[-1]["profile"] == ["deep-tcp-v1"]
    expect(page.locator("#history-pagination")).to_be_hidden()


def test_individual_delete_safe_default_escape_and_undo(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    page.goto(base + "/history")
    wait_for_page(page)
    trigger = page.locator("[data-report-delete]").first
    trigger.click()
    expect(page.locator("#history-delete-cancel")).to_be_focused()
    page.keyboard.press("Escape")
    expect(trigger).to_be_focused()
    assert not controls["delete_calls"]
    trigger.click()
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-delete-dialog")).not_to_be_visible()
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 2")
    wait_for_page(page)
    assert len(controls["delete_calls"]) == 1
    assert len(controls["delete_calls"][0]["reports"]) == 1
    page.locator("#history-undo-delete").click()
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 1")
    assert len(controls["restore_calls"]) == 1 and not controls["deleted"]


def test_select_this_page_is_bounded_and_never_selects_other_pages(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    page.goto(base + "/history")
    wait_for_page(page)
    page.locator("#history-select-all").check()
    expect(page.locator("[data-report-select]:checked")).to_have_count(24)
    expect(page.locator("#history-selection-hint")).to_contain_text("including rows further down")
    page.locator("#history-delete-selected").click()
    expect(page.locator("#history-delete-list li")).to_have_count(24)
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 25")
    wait_for_page(page)
    assert len(controls["delete_calls"]) == 1
    assert len(controls["delete_calls"][0]["reports"]) == 24
    assert len(controls["deleted"]) == 24
    assert controls["reports"][24]["scan_id"] not in controls["deleted"]


def test_partial_delete_keeps_changed_or_active_selections(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    controls["delete_results"] = {
        controls["reports"][1]["scan_id"]: "changed",
        controls["reports"][2]["scan_id"]: "active",
    }
    page.goto(base + "/history")
    wait_for_page(page)
    for index in range(3):
        page.locator("[data-report-select]").nth(index).check()
    page.locator("#history-delete-selected").click()
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-delete-dialog")).not_to_be_visible()
    expect(page.locator("[data-report-select]:checked")).to_have_count(2)
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 2")
    assert len(controls["delete_calls"][0]["reports"]) == 3
    assert controls["deleted"] == {controls["reports"][0]["scan_id"]}


def test_uncertain_failed_delete_is_not_repeated_automatically(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    controls["delete_failure"] = True
    page.goto(base + "/history")
    wait_for_page(page)
    page.locator("[data-report-select]").first.check()
    page.locator("#history-delete-selected").click()
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-delete-error")).to_be_visible()
    expect(page.locator("[data-report-select]:checked")).to_have_count(1)
    page.wait_for_timeout(150)
    assert len(controls["delete_calls"]) == 1 and not controls["deleted"]
    controls["delete_failure"] = False
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-delete-dialog")).not_to_be_visible()
    assert len(controls["delete_calls"]) == 2


def test_pending_delete_disables_duplicate_submission_and_page_changes(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    controls["hold_delete"] = True
    page.goto(base + "/history")
    wait_for_page(page)
    page.locator("[data-report-delete]").first.click()
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-delete-confirm")).to_be_disabled()
    expect(page.locator("#history-delete-cancel")).to_be_disabled()
    page.evaluate("document.querySelector('#history-delete-confirm').click()")
    assert page.locator("#history-pagination [data-page]:enabled").count() == 0
    assert len(controls["delete_calls"]) == 1
    route, payload = controls["held_delete"]
    route.fulfill(json=payload)
    expect(page.locator("#history-delete-dialog")).not_to_be_visible()
    wait_for_page(page)


def test_running_reports_are_ineligible_even_with_full_page_selection(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    controls["reports"][0].update(state="running", phase="service_scan", deletable=False)
    page.goto(base + "/history")
    wait_for_page(page)
    first = page.locator("#history-list > li").first
    expect(first.locator("[data-report-select]")).to_be_disabled()
    expect(first.locator("[data-report-delete]")).to_be_disabled()
    page.locator("#history-select-all").check()
    expect(page.locator("[data-report-select]:checked")).to_have_count(23)
    assert not controls["delete_calls"]


def test_deleting_last_page_item_corrects_page_once(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    controls["report_count"] = 25
    page.goto(base + "/history")
    wait_for_page(page)
    page.locator('#history-pagination [aria-label="Page 2"]').click()
    wait_for_page(page, 1)
    page.locator("[data-report-delete]").click()
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 1")
    wait_for_page(page)
    assert len(calls) == 4 and calls[-1]["offset"] == ["0"]
    expect(page.locator("#history-pagination")).to_be_hidden()


@pytest.mark.parametrize("motion", ["reduce", "no-preference"])
def test_viewport_effect_respects_motion_without_hiding_data_or_mobile_actions(
    history_browser, motion
):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    page.emulate_media(reduced_motion=motion)
    page.set_viewport_size({"width": 320, "height": 844})
    page.goto(base + "/history")
    wait_for_page(page)
    row = page.locator("#history-list > li").first
    row.scroll_into_view_if_needed()
    if motion == "no-preference":
        expect(row).to_have_class("history-report history-reveal")
    duration = row.evaluate("node => parseFloat(getComputedStyle(node).animationDuration)")
    assert duration <= 0.01 if motion == "reduce" else 0 < duration <= 0.5
    row.locator("a").focus()
    assert row.evaluate("node => getComputedStyle(node).opacity") == "1"
    assert len(calls) == 1
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
    page.screenshot(path=controls["artifact_dir"] / ("viewport-history-" + motion + ".png"))
    row.locator("button").click()
    expect(page.locator("#history-delete-cancel")).to_be_focused()
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
