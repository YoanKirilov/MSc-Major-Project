import tomllib
from pathlib import Path

from packaging.requirements import Requirement


def test_lock_pins_satisfy_declared_runtime_and_development_requirements():
    root = Path(__file__).resolve().parents[2]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    pins = {}
    for filename in ("requirements.lock", "requirements-dev.lock"):
        for line in (root / filename).read_text(encoding="utf-8").splitlines():
            if line and not line.startswith(("#", "-r")):
                requirement = Requirement(line)
                pins[requirement.name.lower().replace("_", "-")] = next(
                    iter(requirement.specifier)
                ).version
    for dependency in [*project["dependencies"], *project["optional-dependencies"]["dev"]]:
        requirement = Requirement(dependency)
        assert pins[requirement.name.lower().replace("_", "-")] in requirement.specifier, dependency
