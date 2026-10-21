"""The browser condition helper must retain its condition and bounded deadline."""

from types import SimpleNamespace

import pytest
from tests.fixtures import browser


def test_condition_wait_uses_public_evaluation_and_returns_only_after_success(monkeypatch):
    clock = [0.0]
    values = iter([False, False, True])
    calls = []

    def evaluate(expression, argument):
        calls.append((expression, argument))
        return next(values)

    page = SimpleNamespace(
        evaluate=evaluate, wait_for_timeout=lambda ms: clock.__setitem__(0, clock[0] + ms / 1000)
    )
    monkeypatch.setattr(browser, "monotonic", lambda: clock[0])
    assert browser.wait_for_js(page, "value => value.ready", arg={"ready": True}, timeout=200)
    assert calls == [("value => value.ready", {"ready": True})] * 3
    assert clock[0] == pytest.approx(0.1)


def test_false_condition_stops_at_its_deadline(monkeypatch):
    from playwright.sync_api import TimeoutError as BrowserTimeout

    clock = [0.0]
    page = SimpleNamespace(
        evaluate=lambda *args: False,
        wait_for_timeout=lambda ms: clock.__setitem__(0, clock[0] + ms / 1000),
    )
    monkeypatch.setattr(browser, "monotonic", lambda: clock[0])
    with pytest.raises(BrowserTimeout, match="deadline"):
        browser.wait_for_js(page, "false", timeout=20)
    assert clock[0] == pytest.approx(0.02)


def test_condition_errors_are_not_hidden_as_a_timeout():
    def broken(*args):
        raise ValueError("Synthetic invalid browser expression")

    with pytest.raises(ValueError, match="invalid browser expression"):
        browser.wait_for_js(SimpleNamespace(evaluate=broken), "bad expression")
