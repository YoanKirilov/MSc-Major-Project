import errno
import socket
from types import SimpleNamespace

import pytest
from tests.fixtures import browser


@pytest.mark.parametrize(
    ("scroll_width", "tolerance", "fails"),
    [(320, 0, False), (321, 1, False), (321, 0, True), (322, 1, True)],
)
def test_reflow_diagnostic_keeps_the_callers_original_overflow_limit(
    scroll_width, tolerance, fails
):
    calls = []

    def evaluate(script, limit):
        calls.append(limit)
        return {
            "width": 320,
            "scrollWidth": scroll_width,
            "overflowing": [{"id": "synthetic-oversized-control"}],
        }

    page = SimpleNamespace(evaluate=evaluate)
    if fails:
        with pytest.raises(AssertionError, match="synthetic-oversized-control"):
            browser.assert_page_reflows(page, "Settings at 320px", tolerance=tolerance)
    else:
        browser.assert_page_reflows(page, "Settings at 320px", tolerance=tolerance)
    assert calls == [tolerance]


def test_real_browser_listener_is_high_loopback_and_stays_reserved():
    with browser.browser_listener() as listener:
        host, port = listener.getsockname()
        assert host == "127.0.0.1"
        assert browser.MIN_BROWSER_PORT <= port <= browser.MAX_BROWSER_PORT
        with socket.socket() as competitor, pytest.raises(OSError):
            competitor.bind((host, port))


@pytest.mark.parametrize("code", [errno.EADDRINUSE, errno.EACCES])
def test_browser_listener_closes_collisions_and_retries_only_bounded_local_ports(monkeypatch, code):
    sockets, addresses = [], []

    class Listener:
        closed = False

        def bind(self, address):
            addresses.append(address)
            if len(addresses) == 1:
                raise OSError(code, "Synthetic occupied or reserved port")

        def close(self):
            self.closed = True

    def create(*args):
        listener = Listener()
        sockets.append(listener)
        return listener

    monkeypatch.setattr(browser.socket, "socket", create)
    monkeypatch.setattr(browser.secrets, "randbelow", lambda limit: limit - 1)
    listener = browser.browser_listener()
    assert addresses == [("127.0.0.1", browser.MAX_BROWSER_PORT)] * 2
    assert sockets[0].closed and not listener.closed


@pytest.mark.parametrize("code", [errno.EADDRINUSE, errno.EINVAL])
def test_browser_listener_exhaustion_or_unrelated_error_never_leaks_a_socket(monkeypatch, code):
    sockets = []

    class Listener:
        closed = False

        def bind(self, address):
            assert address[0] == "127.0.0.1"
            raise OSError(code, "Synthetic failure")

        def close(self):
            self.closed = True

    def create(*args):
        listener = Listener()
        sockets.append(listener)
        return listener

    monkeypatch.setattr(browser.socket, "socket", create)
    monkeypatch.setattr(browser.secrets, "randbelow", lambda limit: 0)
    with pytest.raises(RuntimeError if code == errno.EADDRINUSE else OSError):
        browser.browser_listener()
    assert len(sockets) == (browser.PORT_ATTEMPTS if code == errno.EADDRINUSE else 1)
    assert all(listener.closed for listener in sockets)
