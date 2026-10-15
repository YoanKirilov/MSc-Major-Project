"""Report edit/confirmation regressions with isolated facts and forbidden scanners."""

import os

import pytest
from tests.browser_test_ui_ux import _open
from tests.browser_test_ui_ux import ui as ui

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in browsers"),
]


def _guarded(page):
    return page.evaluate(
        """() => { const event = new Event('beforeunload', {cancelable:true});
        window.dispatchEvent(event); return event.defaultPrevented; }"""
    )


def _messages(page):
    page.evaluate("""() => {
        const status = document.querySelector('#report-interaction-status');
        status.textContent = '';
        window.editMessages = [];
        new MutationObserver(() => {
            if (status.textContent) window.editMessages.push(status.textContent);
        }).observe(status, {childList:true, subtree:true, characterData:true});
    }""")


def test_title_save_and_removal_have_one_confirmed_post_close_outcome(ui):
    from playwright.sync_api import expect

    page, _ = _open(ui)
    assert not _guarded(page)
    _messages(page)
    page.locator("#editReportTitle").click()
    page.locator("#annotationEditorInput").fill("  Home review  ")
    assert _guarded(page)
    page.locator("#annotationEditorSave").click()
    expect(page.locator("#annotationEditorDialog")).not_to_be_visible()
    expect(page.locator("#report-user-title")).to_have_text("Home review")
    expect(page.locator("#report-interaction-status")).to_contain_text("title was saved")
    expect(page.locator("#editReportTitle")).to_be_focused()
    assert page.title().startswith("Home review")
    assert len(page.evaluate("window.editMessages")) == 1
    assert not _guarded(page)
    page.locator("#editReportTitle").click()
    page.locator("#annotationEditorInput").fill("")
    page.locator("#annotationEditorSave").click()
    expect(page.locator("#annotationEditorDialog")).not_to_be_visible()
    expect(page.locator("#report-user-title")).to_have_text("")
    expect(page.locator("#report-interaction-status")).to_contain_text("title was removed")
    assert len(page.evaluate("window.editMessages")) == 2
    assert not _guarded(page)


@pytest.mark.parametrize("failure", ["503", "409", "stale", "mismatch"])
def test_unconfirmed_title_receipt_keeps_draft_without_success_or_automatic_retry(ui, failure):
    from playwright.sync_api import expect

    page, report = _open(ui)
    writes = []

    def respond(route):
        request = route.request.post_data_json
        writes.append(request)
        if failure in {"503", "409"}:
            route.fulfill(status=int(failure), json={"detail": "Synthetic save problem"})
        else:
            route.fulfill(
                json={
                    "revision": request["expected_revision"] + int(failure != "stale"),
                    "title": request["title"] if failure == "stale" else "Different title",
                    "action_checks": [],
                }
            )

    page.route(f"**/api/live-scans/{report.scan_id}/title", respond)
    _messages(page)
    page.locator("#editReportTitle").click()
    page.locator("#annotationEditorInput").fill("Keep my title draft")
    page.locator("#annotationEditorSave").click()
    status = page.locator("#annotationEditorStatus")
    expect(status).to_contain_text("not saved" if failure == "409" else "could not be confirmed")
    expect(status).to_contain_text("Your draft is still here")
    expect(page.locator("#annotationEditorInput")).to_have_value("Keep my title draft")
    expect(page.locator("#annotationEditorDialog")).to_be_visible()
    expect(page.locator("#report-user-title")).to_have_text("")
    assert _guarded(page)
    assert len(writes) == 1
    assert page.evaluate("window.editMessages") == []
    page.locator("#annotationEditorCancel").click()
    assert not _guarded(page)


def test_native_leave_warning_can_keep_an_editor_draft_and_cancel_clears_it(ui):
    from playwright.sync_api import expect

    page, base, _ = ui
    page, _ = _open(ui)
    original = page.url
    page.locator("[data-nickname-device]").first.click()
    assert not _guarded(page)
    page.locator("#annotationEditorInput").fill("Unsaved room label")
    assert _guarded(page)
    warnings = []

    def stay(dialog):
        warnings.append(dialog.type)
        dialog.dismiss()

    page.once("dialog", stay)
    page.evaluate("target => { window.location.assign(target); }", base + "/history")
    expect(page.locator("#annotationEditorInput")).to_have_value("Unsaved room label")
    assert page.url == original
    assert warnings == ["beforeunload"]
    page.locator("#annotationEditorCancel").click()
    assert not _guarded(page)
    page.goto(base + "/history")
    expect(page.locator("#history-results-title")).to_be_visible()


def test_even_an_unchanged_pending_title_write_is_guarded_until_confirmed(ui):
    from playwright.sync_api import expect

    page, report = _open(ui)
    pending = []
    page.route(f"**/api/live-scans/{report.scan_id}/title", lambda route: pending.append(route))
    page.locator("#editReportTitle").click()
    assert not _guarded(page)
    page.locator("#annotationEditorSave").click()
    expect(page.locator("#annotationEditorSave")).to_have_text("Saving…")
    assert _guarded(page)
    assert len(pending) == 1
    pending[0].continue_()
    expect(page.locator("#annotationEditorDialog")).not_to_be_visible()
    assert not _guarded(page)


def test_unconfirmed_checklist_draft_is_guarded_until_an_explicit_successful_retry(ui):
    from playwright.sync_api import expect

    page, report = _open(ui)
    endpoint = f"**/api/live-scans/{report.scan_id}/action-checks"
    writes = []

    def fail(route):
        writes.append(route.request.post_data_json)
        route.fulfill(status=503, json={"detail": "Synthetic save unavailable"})

    page.route(endpoint, fail)
    checklist = page.locator("#nextStepsList .next-step-checklist").first
    checklist.locator(":scope > summary").click()
    row = checklist.locator(".action-check").first
    row.locator("select").select_option("checked")
    expect(row.locator(".action-check-note")).to_contain_text("kept here as a draft")
    assert _guarded(page)
    assert len(writes) == 1
    page.unroute(endpoint)
    row.get_by_role("button", name="Save this choice", exact=True).click()
    expect(row.locator(".action-check-note")).to_contain_text("Checklist saved")
    assert not _guarded(page)


def test_hidden_label_characters_are_explained_before_any_write(ui):
    from playwright.sync_api import expect

    page, report = _open(ui)
    writes = []
    page.route(
        f"**/api/live-scans/{report.scan_id}/title",
        lambda route: (writes.append(route.request.post_data_json), route.abort()),
    )
    page.locator("#editReportTitle").click()
    page.locator("#annotationEditorInput").fill("Hidden\u202ename")
    page.locator("#annotationEditorSave").click()
    expect(page.locator("#annotationEditorStatus")).to_contain_text("hidden or control characters")
    expect(page.locator("#annotationEditorInput")).to_have_attribute("aria-invalid", "true")
    expect(page.locator("#annotationEditorInput")).to_be_focused()
    assert _guarded(page)
    assert not writes
    page.locator("#annotationEditorCancel").click()


@pytest.mark.parametrize("dismissal", ["cancel-button", "escape"])
def test_explicit_discard_clears_leave_warning_before_queued_native_close(ui, dismissal):
    page, _ = _open(ui)
    page.locator("#editReportTitle").click()
    page.locator("#annotationEditorInput").fill("Discard this draft")
    assert _guarded(page)
    # Discard and inspect in one browser task: no wait can mask a stale listener.
    guarded = page.evaluate(
        """dismissal => {
            const dialog = document.querySelector('#annotationEditorDialog');
            const cancel = document.querySelector('#annotationEditorCancel');
            if (dismissal === 'cancel-button') cancel.click();
            else dialog.dispatchEvent(new Event('cancel', {cancelable:true}));
            const event = new Event('beforeunload', {cancelable:true});
            window.dispatchEvent(event);
            return {open:dialog.open, guarded:event.defaultPrevented};
        }""",
        dismissal,
    )
    assert guarded == {"open": False, "guarded": False}
