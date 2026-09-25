import asyncio
import webbrowser

import pytest
import uvicorn
from app.cli import main


def test_server_rejects_non_loopback_binding():
    with pytest.raises(SystemExit) as exc:
        main(["serve", "--host", "0.0.0.0", "--no-browser"])

    assert exc.value.code == 2


@pytest.mark.parametrize("no_browser", [False, True])
def test_browser_opens_only_after_server_startup(monkeypatch, capsys, no_browser):
    events = []

    async def startup(server, sockets=None):
        events.append("ready")
        server.started = True

    def run(server):
        asyncio.run(server.startup())

    def open_browser(url):
        assert events == ["ready"]
        assert url.startswith("http://127.0.0.1:8765/#token=")
        events.append("browser")

    monkeypatch.setattr(uvicorn.Server, "startup", startup)
    monkeypatch.setattr(uvicorn.Server, "run", run)
    monkeypatch.setattr(webbrowser, "open", open_browser)
    args = ["serve"] + (["--no-browser"] if no_browser else [])
    assert main(args) == 0
    assert events == (["ready"] if no_browser else ["ready", "browser"])
    assert "Open this local session URL:" in capsys.readouterr().out


def test_failed_startup_does_not_open_an_invalid_session(monkeypatch, capsys):
    async def startup(server, sockets=None):
        raise SystemExit(1)

    def run(server):
        asyncio.run(server.startup())

    def forbidden(_url):
        raise AssertionError("No browser should open when startup failed")

    monkeypatch.setattr(uvicorn.Server, "startup", startup)
    monkeypatch.setattr(uvicorn.Server, "run", run)
    monkeypatch.setattr(webbrowser, "open", forbidden)
    with pytest.raises(SystemExit):
        main(["serve"])
    assert "Open this local session URL:" not in capsys.readouterr().out
