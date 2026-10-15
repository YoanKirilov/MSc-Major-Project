import asyncio
import json
import os

import httpx
import pytest
from app.config import AppConfig
from app.explanations.runtime import OllamaRuntime, launch_local_server
from app.explanations.service import OllamaExplanationProvider


class Child:
    def __init__(self):
        self.returncode = None
        self.terminated = 0

    def terminate(self):
        self.terminated += 1
        self.returncode = 0

    def kill(self):
        self.returncode = -1

    async def wait(self):
        return self.returncode


def provider(handler):
    return OllamaExplanationProvider(model="test-local", transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_existing_server_is_preloaded_with_a_lease_but_never_owned_or_stopped():
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "test-local"}]})
        assert json.loads(request.content) == {
            "model": "test-local",
            "stream": False,
            "keep_alive": "10m",
        }
        return httpx.Response(200, json={"done": True})

    async def forbidden(_):
        pytest.fail("An existing Ollama server must not be replaced")

    runtime = OllamaRuntime(provider(handler), launcher=forbidden)
    assert await runtime.ensure_ready(warm=True)
    assert await runtime.ensure_ready(warm=True)
    assert sum(request.method == "POST" for request in calls) == 1
    assert runtime.state == "ready" and runtime.process is None
    await runtime.close()


@pytest.mark.asyncio
async def test_stopped_server_is_started_once_and_owned_child_is_closed(monkeypatch):
    started = []
    child = Child()

    def handler(request):
        if not started:
            raise httpx.ConnectError("Synthetic stopped server", request=request)
        return httpx.Response(200, json={"models": [{"name": "test-local"}]})

    async def launch(origin):
        started.append(origin)
        return child

    original_sleep = asyncio.sleep
    monkeypatch.setattr("app.explanations.runtime.asyncio.sleep", lambda _: original_sleep(0))
    runtime = OllamaRuntime(provider(handler), launcher=launch)
    assert await runtime.ensure_ready()
    assert await runtime.ensure_ready()
    assert started == ["http://127.0.0.1:11434"]
    await runtime.close()
    assert child.terminated == 1


@pytest.mark.asyncio
async def test_missing_model_does_not_start_another_server_or_download():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"models": []})

    async def forbidden(_):
        pytest.fail("A missing model does not justify spawning another server")

    runtime = OllamaRuntime(provider(handler), launcher=forbidden)
    assert not await runtime.ensure_ready(warm=True)
    assert runtime.state == "missing_model"
    assert [request.url.path for request in calls] == ["/api/tags"]


@pytest.mark.asyncio
async def test_failed_start_is_rate_limited_without_a_restart_loop():
    starts = []

    def handler(request):
        raise httpx.ConnectError("Synthetic offline", request=request)

    async def missing(_):
        starts.append(1)
        raise FileNotFoundError

    runtime = OllamaRuntime(provider(handler), launcher=missing)
    assert not await runtime.ensure_ready()
    assert runtime.state == "not_installed"
    assert not await runtime.ensure_ready()
    assert starts == [1]


@pytest.mark.asyncio
async def test_exited_owned_server_can_recover_after_cooldown(monkeypatch):
    children = []
    online = False

    def handler(request):
        if not online:
            raise httpx.ConnectError("Synthetic crash", request=request)
        return httpx.Response(200, json={"models": [{"name": "test-local"}]})

    async def launch(_):
        nonlocal online
        online = True
        children.append(Child())
        return children[-1]

    original_sleep = asyncio.sleep
    monkeypatch.setattr("app.explanations.runtime.asyncio.sleep", lambda _: original_sleep(0))
    runtime = OllamaRuntime(provider(handler), launcher=launch)
    assert await runtime.ensure_ready()
    children[0].returncode = 1
    online = False
    runtime.next_start = 0
    assert await runtime.ensure_ready()
    assert len(children) == 2
    await runtime.close()
    assert children[0].terminated == 0 and children[1].terminated == 1


@pytest.mark.asyncio
async def test_shutdown_during_start_does_not_orphan_the_owned_child(monkeypatch):
    entered, release = asyncio.Event(), asyncio.Event()
    child = Child()

    def handler(request):
        raise httpx.ConnectError("Synthetic stopped server", request=request)

    async def launch(_):
        entered.set()
        await release.wait()
        return child

    runtime = OllamaRuntime(provider(handler), launcher=launch)
    runtime.start()
    await entered.wait()
    closing = asyncio.create_task(runtime.close())
    await asyncio.sleep(0)
    release.set()
    await closing
    assert child.terminated == 1 and runtime.task is None


@pytest.mark.asyncio
async def test_shutdown_during_a_failed_launch_still_cancels_the_maintenance_loop():
    entered, release = asyncio.Event(), asyncio.Event()

    def handler(request):
        raise httpx.ConnectError("Synthetic stopped server", request=request)

    async def launch(_):
        entered.set()
        await release.wait()
        raise FileNotFoundError

    runtime = OllamaRuntime(provider(handler), launcher=launch)
    runtime.start()
    await entered.wait()
    closing = asyncio.create_task(runtime.close())
    await asyncio.sleep(0)
    release.set()
    await asyncio.wait_for(closing, timeout=1)
    assert runtime.task is None and runtime.process is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "origin",
    [
        "http://example.com:11434",
        "https://localhost:11434",
        "http://user@localhost:11434",
        "http://localhost:11434/api",
    ],
)
async def test_autostart_rejects_nonstandard_origins_before_launch(origin):
    with pytest.raises(ValueError):
        await launch_local_server(origin)


def test_autostart_default_and_opt_out(monkeypatch):
    monkeypatch.delenv("APP_AI_AUTOSTART")
    assert AppConfig.from_env().ai_autostart
    monkeypatch.setenv("APP_AI_AUTOSTART", "0")
    assert not AppConfig.from_env().ai_autostart


@pytest.mark.asyncio
async def test_slow_server_initialisation_is_waited_for_without_restarting(monkeypatch):
    attempts = []

    def handler(request):
        attempts.append(1)
        if len(attempts) < 3:
            raise httpx.ReadTimeout("Synthetic hardware discovery", request=request)
        return httpx.Response(200, json={"models": [{"name": "test-local"}]})

    async def forbidden(_):
        pytest.fail("Do not replace a server that is starting slowly")

    original_sleep = asyncio.sleep
    monkeypatch.setattr("app.explanations.runtime.asyncio.sleep", lambda _: original_sleep(0))
    runtime = OllamaRuntime(provider(handler), launcher=forbidden)
    assert await runtime.wait_ready(timeout_s=1)
    assert len(attempts) == 3 and runtime.state == "ready"


@pytest.mark.asyncio
async def test_waiting_for_unresponsive_runtime_has_an_overall_deadline():
    def handler(request):
        raise httpx.ReadTimeout("Synthetic stuck server", request=request)

    runtime = OllamaRuntime(provider(handler))
    assert not await runtime.wait_ready(timeout_s=0.01)
    assert runtime.state == "startup_timeout"


@pytest.mark.asyncio
async def test_spawn_is_hidden_local_only_and_uses_no_shell_or_download(monkeypatch):
    captured = []

    async def spawn(*args, **kwargs):
        captured.append((args, kwargs))
        return Child()

    monkeypatch.setattr("app.explanations.runtime.ollama_executable", lambda: "installed-ollama")
    monkeypatch.setattr("app.explanations.runtime.asyncio.create_subprocess_exec", spawn)
    await launch_local_server("http://127.0.0.1:11434")
    args, options = captured[0]
    assert args == ("installed-ollama", "serve")
    assert options["env"]["OLLAMA_HOST"] == "127.0.0.1:11434"
    assert options["env"]["OLLAMA_NO_CLOUD"] == "1"
    assert "shell" not in options
    if os.name == "nt":
        assert options["creationflags"] != 0


def test_app_lifespan_wires_and_closes_the_configured_maintenance(monkeypatch):
    from app.main import create_app
    from fastapi.testclient import TestClient

    events = []

    class Runtime:
        def __init__(self, provider):
            self.provider = provider

        def start(self):
            events.append("start")

        async def close(self):
            events.append("close")

    monkeypatch.setenv("APP_AI_AUTOSTART", "1")
    monkeypatch.setattr("app.main.OllamaRuntime", Runtime)
    app = create_app()
    with TestClient(app):
        assert app.state.explanations.provider.runtime is app.state.ollama_runtime
        assert events == ["start"]
    assert events == ["start", "close"]
