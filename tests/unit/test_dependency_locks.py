import tomllib
from pathlib import Path

from packaging.requirements import Requirement


def test_lock_pins_satisfy_declared_runtime_and_development_requirements():
    root = Path(__file__).resolve().parents[2]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    pins = {}
    pending = [root / "requirements.lock", root / "requirements-dev.lock"]
    visited = set()
    while pending:
        path = pending.pop().resolve()
        assert path.is_relative_to(root), "Lock includes must remain in the project"
        if path in visited:
            continue
        visited.add(path)
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("-r "):
                pending.append(path.parent / line[3:].strip())
                continue
            requirement = Requirement(line)
            specifiers = list(requirement.specifier)
            assert len(specifiers) == 1 and specifiers[0].operator == "==", line
            name = requirement.name.lower().replace("_", "-")
            version = specifiers[0].version
            assert name not in pins or pins[name] == version, f"Conflicting pins for {name}"
            pins[name] = version
    for dependency in [*project["dependencies"], *project["optional-dependencies"]["dev"]]:
        requirement = Requirement(dependency)
        assert pins[requirement.name.lower().replace("_", "-")] in requirement.specifier, dependency
