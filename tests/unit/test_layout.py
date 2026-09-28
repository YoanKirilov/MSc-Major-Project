"""Protect source organisation without importing modules or starting the app."""

import ast
from importlib.util import resolve_name
from pathlib import Path


def test_application_modules_are_reachable_from_the_entry_point():
    root = Path(__file__).resolve().parents[2]
    modules = {}
    for path in (root / "app").rglob("*.py"):
        parts = list(path.relative_to(root).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        modules[".".join(parts)] = path

    edges = {}
    for name, path in modules.items():
        package = name if path.name == "__init__.py" else name.rpartition(".")[0]
        imports = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imports.update(item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                target = ("." * node.level) + (node.module or "")
                target = resolve_name(target, package) if node.level else target
                imports.add(target)
                imports.update(f"{target}.{item.name}" for item in node.names)
        # Importing a module also executes any containing package initialisers.
        edges[name] = {
            prefix
            for target in imports
            for i in range(1, len(target.split(".")) + 1)
            if (prefix := ".".join(target.split(".")[:i])) in modules
        }

    visited = set()
    pending = ["app.__main__"]
    while pending:
        name = pending.pop()
        if name not in visited:
            visited.add(name)
            pending.extend(edges[name] - visited)
    unused = sorted(
        name for name, path in modules.items() if name not in visited and path.name != "__init__.py"
    )
    assert not unused, f"Review unreferenced application modules before cleanup: {unused}"


def test_service_keeps_the_same_pure_validation_entry_point():
    from app.explanations.service import ExplanationService
    from app.explanations.validation import validated_line

    assert ExplanationService._validated_line is validated_line
