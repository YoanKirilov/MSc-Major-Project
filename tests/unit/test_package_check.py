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
    (tmp_path / "pyproject.toml").write_text("[project]\nname='example'\n")
    (tmp_path / "README.md").write_text("Synthetic package")
    (tmp_path / "app").mkdir()
    (tmp_path / "app/__init__.py").write_text("")
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
            assert kwargs["cwd"] != tmp_path
            assert kwargs["cwd"].name == "source"
            assert (kwargs["cwd"] / "app/__init__.py").is_file()
            wheels = Path(command[command.index("--outdir") + 1])
            wheels.mkdir()
            (wheels / "synthetic-project.whl").write_bytes(b"not executed")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(check_package.venv, "EnvBuilder", Builder)
    bootstraps = []
    monkeypatch.setattr(
        check_package,
        "bootstrap_trust",
        lambda python, folder, **kwargs: bootstraps.append((python, folder, kwargs)),
    )
    monkeypatch.setattr(check_package.subprocess, "run", run)
    wheelhouse = tmp_path / "local-wheels"
    wheelhouse.mkdir()
    assert check_package.main(["--offline", "--wheelhouse", str(wheelhouse)]) == 0
    assert [env.name for env in environments] == ["build-venv", "venv"]
    assert len(bootstraps) == 2 and all(item[2] == {"offline": True} for item in bootstraps)
    installs = [command for command in commands if "install" in command]
    assert len(installs) == 2
    assert all("--no-index" in command and "--find-links" in command for command in installs)
    assert str(tmp_path / "requirements-build.lock") in installs[0]
    build = next(command for command in commands if "build" in command)
    assert "--no-isolation" in build
    assert "build-venv" in build[0]
    assert "-I" in commands[-1]
    assert "verify_package.py" in commands[-1][-1]


def test_source_snapshot_excludes_stale_builds_caches_and_private_data(tmp_path):
    root = tmp_path / "checkout"
    root.mkdir()
    for name in ("README.md", "pyproject.toml"):
        (root / name).write_bytes(b"current metadata\n")
    (root / "app/api").mkdir(parents=True)
    (root / "app/api/scans.py").write_bytes(b"current module\n")
    (root / "app/__pycache__").mkdir()
    (root / "app/__pycache__/old.pyc").write_bytes(b"old cache")
    stale = root / "build/lib/app/api/monitoring.py"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"deleted scheduler")
    (root / ".env").write_bytes(b"private settings")
    (root / "data").mkdir()
    (root / "data/scan.json").write_bytes(b"private scan")
    target = tmp_path / "clean-source"
    assert check_package.source_snapshot(root, target) == target
    assert (target / "app/api/scans.py").read_bytes() == b"current module\n"
    assert sorted(
        path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()
    ) == ["README.md", "app/api/scans.py", "pyproject.toml"]
    assert stale.read_bytes() == b"deleted scheduler", "Never delete checkout build data"
    with pytest.raises(FileExistsError):
        check_package.source_snapshot(root, target)
