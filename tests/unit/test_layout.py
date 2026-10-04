"""Protect source organisation without importing modules or starting the app."""

import ast
import re
from importlib.util import resolve_name
from pathlib import Path
from urllib.parse import urlsplit


def test_run_again_waits_for_loaded_report():
    template = Path(__file__).resolve().parents[2] / "app/templates/scan.html"
    button = re.search(r'<button\b[^>]*id="runAgainButton"[^>]*>', template.read_text())
    assert button is not None
    assert re.search(r"\bdisabled\b", button.group())


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


def test_shipped_templates_and_assets_are_reachable_from_pages():
    """Catch orphan files and broken local links before deleting or packaging assets."""
    app = Path(__file__).resolve().parents[2] / "app"
    templates = app / "templates"
    static = app / "static"
    tree = ast.parse((app / "main.py").read_text(encoding="utf-8"))
    pending = [
        templates / keyword.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "TemplateResponse"
        for keyword in node.keywords
        if keyword.arg == "name" and isinstance(keyword.value, ast.Constant)
    ]
    visited = set()
    while pending:
        path = pending.pop().resolve()
        if path in visited:
            continue
        assert path.is_relative_to(app), f"Page dependency escaped app directory: {path}"
        assert path.is_file(), f"Missing page dependency: {path}"
        visited.add(path)
        content = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            pending.extend(
                templates / name
                for name in re.findall(r"{%\s*(?:extends|include)\s+['\"]([^'\"]+)", content)
            )
            references = re.findall(r"(?:src|href)=['\"]([^'\"]+)", content)
        elif path.suffix in {".js", ".mjs"}:
            references = re.findall(r"(?:\bfrom\s*|\bimport\s*)['\"]([^'\"]+)", content)
        elif path.suffix == ".css":
            references = re.findall(r"url\(\s*['\"]?([^'\")\s]+)", content)
        else:
            references = []
        for reference in references:
            url = urlsplit(reference)
            if url.scheme or url.netloc:
                continue
            if url.path.startswith("/static/"):
                pending.append(static / url.path.removeprefix("/static/"))
            elif url.path.startswith(("./", "../")):
                pending.append(path.parent / url.path)
    shipped = {
        path.resolve()
        for folder in (templates, static)
        for path in folder.rglob("*")
        if path.is_file()
    }
    assert not shipped - visited, f"Review orphan page/assets: {sorted(shipped - visited)}"
