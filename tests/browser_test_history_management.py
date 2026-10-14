"""Bounded history pages and confirmed deletion, using intercepted synthetic data."""

import os

import pytest
from tests import browser_test_history_scroll as history_cases

# Reuse the isolated, engine-parametrized fixture without importing test cases.
history_browser = history_cases.history_browser
reveal_with_keyboard = history_cases.reveal_with_keyboard

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browser"),
]


def test_pages_cap_at_24_and_navigation_replaces_the_page(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")
    assert not calls
    for count in range(1, 25):
        reveal_with_keyboard(page, count)
    expect(page.locator("#history-list a")).to_have_count(24)
    expect(page.locator("#history-list a").last).to_contain_text("Saved report 24")
    assert len(calls) == 1
    for _ in range(3):
        reveal_with_keyboard(page, 24)
    assert len(calls) == 1
    expect(page.locator("#history-pagination-bottom")).to_be_visible()
    page.locator('#history-pagination-bottom [data-page="2"]').first.click()
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 25")
    expect(page.locator("#history-list a")).to_have_count(1)
    assert calls[-1]["offset"] == ["24"]
    for count in range(2, 25):
        reveal_with_keyboard(page, count)
    expect(page.locator("#history-list a").last).to_contain_text("Saved report 48")
    page.locator('#history-pagination-bottom [data-page="3"]').first.click()
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 49")
    for count in range(2, 6):
        reveal_with_keyboard(page, count)
    reveal_with_keyboard(page, 5)
    assert len(calls) == 3
    assert [call["offset"] for call in calls] == [["0"], ["24"], ["48"]]
    assert all(call["limit"] == ["24"] for call in calls)
    expect(page.locator('#history-pagination [data-page="3"]')).to_have_attribute(
        "aria-current", "page"
    )


def test_filters_reset_page_and_selection_without_loading_before_scroll(history_browser):
    from playwright.sync_api import expect

    page, base, calls, _ = history_browser
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    page.locator('#history-pagination [data-page="2"]').first.click()
    expect(page.locator("#history-list a")).to_contain_text("Saved report 25")
    page.locator("[data-report-select]").check()
    expect(page.locator("#history-delete-selected")).to_be_enabled()
    page.locator("#history-profile").select_option("deep-tcp-v1")
    page.get_by_role("button", name="Search reports", exact=True).click()
    expect(page.locator("#history-list a")).to_have_count(0)
    expect(page.locator("#history-delete-selected")).to_be_disabled()
    previous_calls = len(calls)
    page.wait_for_timeout(150)
    assert len(calls) == previous_calls
    reveal_with_keyboard(page, 1)
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 2")
    assert calls[-1]["offset"] == ["0"]
    assert calls[-1]["profile"] == ["deep-tcp-v1"]
    for count in range(2, 19):
        reveal_with_keyboard(page, count)
    reveal_with_keyboard(page, 18)
    expect(page.locator("#history-list a")).to_have_count(18)
    expect(page.locator("#history-pagination")).to_be_hidden()


def test_individual_delete_requires_confirmation_and_supports_undo(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    trigger = page.locator("[data-report-delete]").first
    trigger.click()
    dialog = page.locator("#history-delete-dialog")
    expect(dialog).to_be_visible()
    expect(page.locator("#history-delete-cancel")).to_be_focused()
    assert not controls["delete_calls"]
    page.locator("#history-delete-cancel").click()
    expect(dialog).not_to_be_visible()
    expect(trigger).to_be_focused()
    expect(page.locator("#history-list a")).to_contain_text("Saved report 1")
    trigger.click()
    page.keyboard.press("Escape")
    expect(dialog).not_to_be_visible()
    assert not controls["delete_calls"]
    trigger.click()
    page.locator("#history-delete-confirm").click()
    expect(dialog).not_to_be_visible()
    expect(page.locator("#history-list a")).to_contain_text("Saved report 2")
    assert len(controls["delete_calls"]) == 1
    assert len(controls["delete_calls"][0]["reports"]) == 1
    assert len(controls["deleted"]) == 1
    undo = page.locator("#history-undo-delete")
    expect(undo).to_be_visible()
    undo.click()
    expect(page.locator("#history-list a")).to_contain_text("Saved report 1")
    assert len(controls["restore_calls"]) == 1
    assert not controls["deleted"]


def test_select_all_applies_only_to_displayed_reports_and_bulk_delete_is_one_request(
    history_browser,
):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    page.goto(base + "/history")
    for count in range(1, 5):
        reveal_with_keyboard(page, count)
    checkboxes = page.locator("[data-report-select]")
    expect(checkboxes).to_have_count(4)
    page.locator("#history-select-all").check()
    expect(page.locator("[data-report-select]:checked")).to_have_count(4)
    page.locator("#history-delete-selected").click()
    expect(page.locator("#history-delete-dialog")).to_be_visible()
    expect(page.locator("#history-delete-title")).to_contain_text("4")
    assert not controls["delete_calls"]
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-delete-dialog")).not_to_be_visible()
    assert len(controls["delete_calls"]) == 1
    deleted = controls["delete_calls"][0]["reports"]
    assert len(deleted) == 4
    assert {item["scan_id"] for item in deleted} == {
        report["scan_id"] for report in controls["reports"][:4]
    }
    assert len(controls["deleted"]) == 4
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 5")
    expect(page.locator("[data-report-select]:checked")).to_have_count(0)


def test_partial_delete_keeps_failed_report_selections(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    controls["delete_results"] = {
        controls["reports"][1]["scan_id"]: "changed",
        controls["reports"][2]["scan_id"]: "active",
    }
    page.goto(base + "/history")
    for count in (1, 2, 3):
        reveal_with_keyboard(page, count)
    page.locator("#history-select-all").check()
    page.locator("#history-delete-selected").click()
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-delete-dialog")).not_to_be_visible()
    expect(page.locator("#history-list a").first).to_contain_text("Saved report 2")
    expect(page.locator("[data-report-select]:checked")).to_have_count(2)
    expect(page.locator("#history-delete-selected")).to_be_enabled()
    assert len(controls["delete_calls"]) == 1
    assert len(controls["delete_calls"][0]["reports"]) == 3
    assert controls["deleted"] == {controls["reports"][0]["scan_id"]}
    expect(page.locator("#history-feedback")).to_contain_text("not")


def test_failed_delete_preserves_reports_and_selection_until_retry(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    controls["delete_failure"] = True
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    page.locator("[data-report-select]").check()
    page.locator("#history-delete-selected").click()
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-delete-dialog")).to_be_visible()
    expect(page.locator("#history-delete-confirm")).to_be_enabled()
    expect(page.locator("#history-delete-dialog")).to_contain_text("Synthetic delete unavailable.")
    expect(page.locator("[data-report-select]:checked")).to_have_count(1)
    expect(page.locator("#history-list a")).to_contain_text("Saved report 1")
    assert not controls["deleted"]
    controls["delete_failure"] = False
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-delete-dialog")).not_to_be_visible()
    expect(page.locator("#history-list a")).to_contain_text("Saved report 2")
    assert len(controls["delete_calls"]) == 2


def test_busy_delete_disables_duplicate_submission_and_pagination(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    controls["hold_delete"] = True
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    page.locator("[data-report-delete]").click()
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-delete-confirm")).to_be_disabled()
    expect(page.locator("#history-delete-cancel")).to_be_disabled()
    page.evaluate("document.querySelector('#history-delete-confirm').click()")
    page.wait_for_timeout(150)
    assert len(controls["delete_calls"]) == 1
    assert page.locator("#history-pagination [data-page]:enabled").count() == 0
    route, payload = controls["held_delete"]
    controls["hold_delete"] = False
    route.fulfill(json=payload)
    expect(page.locator("#history-delete-dialog")).not_to_be_visible()
    expect(page.locator("#history-list a")).to_contain_text("Saved report 2")
    assert len(controls["delete_calls"]) == 1


def test_running_report_cannot_be_selected_or_deleted(history_browser):
    from playwright.sync_api import expect

    page, base, _, controls = history_browser
    controls["reports"][0].update(state="running", phase="services", deletable=False)
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    first = page.locator("#history-list > li").first
    expect(first).to_contain_text("In progress")
    assert first.locator("[data-report-select]:enabled, [data-report-delete]:enabled").count() == 0
    expect(page.locator("#history-delete-selected")).to_be_disabled()
    reveal_with_keyboard(page, 2)
    page.locator("#history-select-all").check()
    expect(page.locator("[data-report-select]:checked")).to_have_count(1)
    assert not controls["delete_calls"]


def test_deleting_last_item_on_last_page_returns_to_valid_page(history_browser):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    controls["report_count"] = 25
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    page.locator('#history-pagination [data-page="2"]').first.click()
    expect(page.locator("#history-list a")).to_contain_text("Saved report 25")
    page.locator("[data-report-delete]").click()
    page.locator("#history-delete-confirm").click()
    expect(page.locator("#history-delete-dialog")).not_to_be_visible()
    expect(page.locator("#history-list a")).to_contain_text("Saved report 1")
    expect(page.locator("#history-list a")).to_have_count(1)
    assert calls[-1]["offset"] == ["0"]
    assert len(calls) == 4  # First page, last page, refresh, bounded correction.
    expect(page.locator("#history-pagination")).to_be_hidden()
    assert len(controls["deleted"]) == 1


@pytest.mark.parametrize("motion", ["reduce", "no-preference"])
def test_reveal_motion_respects_preferences_without_mobile_overflow(history_browser, motion):
    from playwright.sync_api import expect

    page, base, calls, controls = history_browser
    page.emulate_media(reduced_motion=motion)
    page.set_viewport_size({"width": 320, "height": 844})
    page.goto(base + "/history")
    reveal_with_keyboard(page, 1)
    expect(page.locator("#history-list a")).to_be_visible()
    duration = page.locator("#history-list > li").first.evaluate(
        """element => {
            const style = getComputedStyle(element);
            return Math.max(...[style.animationDuration, style.transitionDuration]
                .flatMap(value => value.split(',').map(part => parseFloat(part))));
        }"""
    )
    if motion == "reduce":
        assert duration <= 0.01, duration
    else:
        assert 0 < duration <= 0.5, duration
    assert len(calls) == 1
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    page.screenshot(
        path=str(controls["artifact_dir"] / f"history-mobile-{motion}.png"), full_page=True
    )
    page.locator("[data-report-delete]").click()
    expect(page.locator("#history-delete-dialog")).to_be_visible()
    expect(page.locator("#history-delete-cancel")).to_be_focused()
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    page.screenshot(path=str(controls["artifact_dir"] / f"history-delete-{motion}.png"))
