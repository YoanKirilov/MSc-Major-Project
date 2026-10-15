"""Screenshot-request geometry, using synthetic reports and blocked scan/provider I/O."""

import os

import pytest
from tests.browser_test_ui_ux import _open
from tests.browser_test_ui_ux import ui as ui

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in browsers"),
]


@pytest.mark.parametrize("width", [320, 768, 1440])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_report_search_and_device_actions_have_one_clear_shape(ui, width, theme):
    page, _ = _open(ui, size=(width, 900))
    page.evaluate(
        """theme => {
            document.documentElement.dataset.theme = theme;
            document.documentElement.dataset.textSize = 'larger';
        }""",
        theme,
    )
    dimensions = page.locator(".device-action-buttons").evaluate_all(
        """groups => groups.map(group => [...group.querySelectorAll('button')].map(button => {
            const rect = button.getBoundingClientRect();
            return {width: rect.width, height: rect.height, client: button.clientWidth,
                scroll: button.scrollWidth};
        }))"""
    )
    assert dimensions
    for buttons in dimensions:
        assert len(buttons) == 2
        assert abs(buttons[0]["width"] - buttons[1]["width"]) < 1
        assert abs(buttons[0]["height"] - buttons[1]["height"]) < 1
        assert all(button["height"] >= 44 for button in buttons)
        assert all(button["scroll"] <= button["client"] + 1 for button in buttons)
    for selector in ("#deviceSearchInput", "#searchInput"):
        geometry = page.locator(selector).evaluate(
            """input => ({
                outer: getComputedStyle(input.parentElement).borderTopWidth,
                inner: getComputedStyle(input).borderTopWidth,
                input: input.getBoundingClientRect().height,
                clear: input.parentElement.querySelector('button').getBoundingClientRect().height
            })"""
        )
        assert geometry["outer"] == "0px"
        assert float(geometry["inner"].replace("px", "")) > 0
        assert geometry["input"] >= 44 and geometry["clear"] >= 44
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"
    )


def test_navigation_colour_underline_and_help_spacing(ui):
    from playwright.sync_api import expect

    page, base, _ = ui
    for route, hint in (
        ("/history", "#history-date-help"),
        ("/devices", "#device-library-applied"),
    ):
        page.goto(base + route)
        expect(page.locator(hint)).not_to_be_empty()
        spacing = page.locator(hint).evaluate(
            """hint => {
                const form = hint.previousElementSibling;
                const field = form.querySelector('.form-field');
                const input = field.querySelector('input');
                const fieldHint = field.querySelector('.field-hint');
                const buttons = [...form.querySelectorAll('.form-actions > button')];
                const gap = (below, above) => below.getBoundingClientRect().top
                    - above.getBoundingClientRect().bottom;
                return {
                    actionHelp: gap(hint, form),
                    fieldHelp: gap(fieldHint, input),
                    actionMargin: getComputedStyle(form.querySelector('.form-actions')).marginTop,
                    fieldPadding: getComputedStyle(input).paddingLeft,
                    buttonPadding: buttons.map(button => getComputedStyle(button).paddingLeft),
                    buttonHeights: buttons.map(button => button.getBoundingClientRect().height)
                };
            }"""
        )
        assert abs(spacing["actionHelp"] - spacing["fieldHelp"]) < 1
        assert spacing["fieldHelp"] == 8
        assert spacing["actionMargin"] == "0px"
        assert all(padding == spacing["fieldPadding"] for padding in spacing["buttonPadding"])
        assert all(height == 48 for height in spacing["buttonHeights"])
        colours = page.locator(".topbar-actions > a").evaluate_all(
            """links => links.map(link => ({colour: getComputedStyle(link).color,
                offset: parseFloat(getComputedStyle(link).textUnderlineOffset),
                size: parseFloat(getComputedStyle(link).fontSize),
                skip: getComputedStyle(link).textDecorationSkipInk}))"""
        )
        assert len({link["colour"] for link in colours}) == 1
        assert all(link["offset"] >= link["size"] * 0.35 for link in colours)
        assert all(link["skip"] == "auto" for link in colours)
        current = page.locator('.topbar-actions > a[aria-current="page"]')
        before = current.evaluate("element => getComputedStyle(element).color")
        current.hover()
        assert current.evaluate("element => getComputedStyle(element).color") != before
        page.mouse.move(0, 0)


@pytest.mark.parametrize("width", [320, 1440])
def test_device_actions_are_compact_centred_and_still_easy_to_tap(ui, width, tmp_path):
    page, _ = _open(ui, size=(width, 900))
    sizes = page.locator(".device-action-buttons").evaluate_all(
        """groups => groups.map(group => {
            const rect = group.getBoundingClientRect();
            const footer = group.parentElement.getBoundingClientRect();
            return {width: rect.width, centre: rect.left + rect.width / 2,
                footerCentre: footer.left + footer.width / 2,
                heights: [...group.children].map(button => button.getBoundingClientRect().height)};
        })"""
    )
    assert sizes
    for group in sizes:
        assert group["width"] <= 256
        assert abs(group["centre"] - group["footerCentre"]) < 1
        assert all(44 <= height <= 60 for height in group["heights"])
    page.locator(".device-summary-group").first.screenshot(
        path=str(tmp_path / f"device-actions-{width}.png")
    )
