"""Synthetic native-control semantics and interaction, not actual AT certification."""

import os

import pytest
from tests.browser_test_ui_ux import _open
from tests.browser_test_ui_ux import ui as ui

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in browsers"),
]


def test_supporting_dialog_contains_keyboard_focus_and_preserves_page_with_text_spacing(ui):
    from playwright.sync_api import expect

    page, _ = _open(ui, size=(320, 568))
    # Exercise the same user text-spacing overrides without injecting an inline
    # stylesheet, which the application's enforced CSP deliberately rejects.
    page.evaluate("""() => {
        for (const element of document.querySelectorAll('*')) {
            element.style.setProperty('line-height', '1.5', 'important');
            element.style.setProperty('letter-spacing', '.12em', 'important');
            element.style.setProperty('word-spacing', '.16em', 'important');
        }
        for (const element of document.querySelectorAll('p'))
            element.style.setProperty('margin-bottom', '2em', 'important');
    }""")
    trigger = page.locator('[data-supporting-topic="accessibility"]')
    trigger.scroll_into_view_if_needed()
    trigger.focus()
    before = page.evaluate("scrollY")
    page.keyboard.press("Enter")
    dialog = page.locator("#supportingInfoDialog")
    expect(dialog).to_be_visible()
    expect(page.locator("#supportingInfoTitle")).to_be_focused()
    for key in ["Tab"] * 10 + ["Shift+Tab"] * 10:
        page.keyboard.press(key)
        assert dialog.evaluate("element => element.contains(document.activeElement)"), (
            key,
            page.evaluate("document.activeElement.outerHTML.slice(0, 500)"),
        )
        bounds = page.evaluate(
            """() => { const r=document.activeElement.getBoundingClientRect();
                return {top:r.top,bottom:r.bottom,left:r.left,right:r.right}; }"""
        )
        assert bounds["bottom"] > 0 and bounds["top"] < 568
        assert bounds["left"] >= 0 and bounds["right"] <= 321
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    page.keyboard.press("Escape")
    expect(dialog).not_to_be_visible()
    expect(trigger).to_be_focused()
    assert abs(page.evaluate("scrollY") - before) < 2


def test_visible_native_controls_have_visible_names_and_valid_descriptions(ui):
    page, base, _ = ui
    page, _ = _open(ui)
    for route in (page.url, base + "/devices", base + "/settings", base + "/history"):
        page.goto(route)
        page.wait_for_load_state("networkidle")
        problems = page.locator("button,input,select").evaluate_all(
            r"""controls => controls.filter(control => control.checkVisibility())
            .flatMap(control => {
                const problems=[];
                const text=control.innerText?.trim() || '';
                const label=control.getAttribute('aria-label');
                const references=(control.getAttribute('aria-labelledby') || '').split(/\s+/)
                    .map(id => document.getElementById(id)?.textContent || '').join(' ').trim();
                if (control.tagName === 'BUTTON' && !text && !label && !references)
                    problems.push('Unnamed button: ' + control.outerHTML.slice(0,180));
                if (label && text && !label.toLowerCase().includes(text.toLowerCase()))
                    problems.push('Visible label omitted: ' + control.id);
                if (['INPUT','SELECT'].includes(control.tagName) && !control.labels?.length
                    && !label && !control.getAttribute('aria-labelledby'))
                    problems.push('Unlabelled field: ' + control.id);
                for (const id of (control.getAttribute('aria-describedby') || '').split(/\s+/))
                    if (id && !document.getElementById(id))
                        problems.push('Missing description: '+id);
                return problems;
            })"""
        )
        assert not problems, (route, problems)


def test_home_and_report_explain_disabled_javascript_without_starting_work(ui):
    from playwright.sync_api import expect

    page, base, reports = ui
    context = page.context.browser.new_context(java_script_enabled=False)
    forbidden = []

    def guard(route):
        if not route.request.url.startswith(base + "/") or route.request.method != "GET":
            forbidden.append((route.request.method, route.request.url))
            route.abort()
        else:
            route.continue_()

    context.route("**/*", guard)
    try:
        disabled = context.new_page()
        disabled.goto(base + "/")
        # Playwright's text matcher deliberately skips NOSCRIPT containers;
        # inspect the actual rendered warning, not that container's special text.
        warning = disabled.locator("noscript .status-message")
        expect(warning).to_be_visible()
        expect(warning).to_contain_text("No scan was started")
        expect(disabled.locator("#scanLaunchButton")).to_be_disabled()
        disabled.goto(base + "/scans/" + reports["rich"].scan_id)
        expect(warning).to_be_visible()
        expect(warning).to_contain_text("Your saved results remain")
    finally:
        context.close()
    assert not forbidden
