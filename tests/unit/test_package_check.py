from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts import check_package


@pytest.mark.parametrize("options", [["--offline"], ["--wheelhouse", "does-not-exist"]])
def test_invalid_package_options_do_not_start_installs(monkeypatch, options):
    monkeypatch.setattr(
        check_package.subprocess, "run", lambda *a, **k: pytest.fail("Do not install")
    )
    with pytest.raises(SystemExit) as error:
        check_package.main(options)
    assert error.value.code == 2


def test_package_build_is_pinned_and_offline_index_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(check_package, "__file__", str(tmp_path / "scripts/check_package.py"))
    environments, commands = [], []

    class Builder:
        def __init__(self, *, with_pip):
            assert with_pip

        def create(self, path):
            environments.append(path)
            path.mkdir()

    def run(command, **kwargs):
        assert kwargs["check"]
        commands.append(command)
        if "build" in command:
            wheels = Path(command[command.index("--outdir") + 1])
            wheels.mkdir()
            (wheels / "synthetic-project.whl").write_bytes(b"not executed")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(check_package.venv, "EnvBuilder", Builder)
    monkeypatch.setattr(check_package.subprocess, "run", run)
    wheelhouse = tmp_path / "local-wheels"
    wheelhouse.mkdir()
    assert check_package.main(["--offline", "--wheelhouse", str(wheelhouse)]) == 0
    assert [env.name for env in environments] == ["build-venv", "venv"]
    installs = [command for command in commands if "install" in command]
    assert len(installs) == 2
    assert all("--no-index" in command and "--find-links" in command for command in installs)
    assert str(tmp_path / "requirements-build.lock") in installs[0]
    build = next(command for command in commands if "build" in command)
    assert "--no-isolation" in build
    assert "build-venv" in build[0]
    assert "-I" in commands[-1]
    assert "verify_package.py" in commands[-1][-1]
