"""Keep application dependencies and presentation at their approved boundaries."""

import ast
from pathlib import Path


def test_application_import_boundaries() -> None:
    root = Path(__file__).parents[1]
    modules = {
        ".".join(path.relative_to(root).with_suffix("").parts).removesuffix(".__init__"): path
        for path in (root / "app").rglob("*.py")
    }
    cli_inputs = set(
        "app.cli app.discovery app.env app.machine app.managers app.models app.reporting app.shell "
        "app.ops.files app.ops.packages app.ops.scripts".split()
    )
    allowed = {
        "app": set(),
        "app.__main__": {"app.cli.entry"},
        "app.models": set(),
        "app.env": {"app.models"},
        "app.discovery": {"app.env"},
        "app.machine": {"app.discovery", "app.env", "app.models"},
        "app.managers": {"app.env", "app.models", "app.ops.scripts", "app.shell"},
        "app.reporting": set(),
        "app.shell": {"app.env", "app.reporting"},
        "app.ops": set(),
        "app.ops.files": {"app.env", "app.models", "app.shell"},
        "app.ops.packages": {"app.models", "app.managers", "app.shell"},
        "app.ops.scripts": {"app.env", "app.shell"},
        "app.cli": {"app.discovery", "app.env"},
        "app.cli.entry": {
            "app.cli",
            "app.reporting",
            *(f"app.cli.{name}" for name in ("deploy", "upgrade", "sync", "info")),
        },
        **{f"app.cli.{name}": cli_inputs for name in ("deploy", "upgrade", "sync", "info")},
    }
    assert modules.keys() <= allowed.keys(), "Declare dependency boundaries for new modules"

    for module, path in modules.items():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: dict[str, str] = {}
        references = []

        # Resolve direct, aliased, and relative imports to their actual modules.
        for node in ast.walk(tree):
            if not isinstance(node, ast.Import | ast.ImportFrom):
                continue
            base = ""
            if isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
                    parents = package.split(".")
                    base = ".".join([*parents[: len(parents) - node.level + 1], base]).rstrip(".")
            for alias in node.names:
                reference = f"{base}.{alias.name}" if base else alias.name
                name = alias.asname or alias.name
                if isinstance(node, ast.Import) and not alias.asname:
                    name = alias.name.split(".")[0]
                    imported[name] = name
                else:
                    imported[name] = reference
                references.append((node.lineno, reference))

        # Check module attributes too, including aliases and imported public objects.
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id != "settings", f"{path}:{node.lineno}: global settings consumer"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "print" or module == "app.reporting", (
                    f"{path}:{node.lineno}: direct print outside reporting"
                )
            if not isinstance(node, ast.Attribute):
                continue
            parts = []
            value = node
            while isinstance(value, ast.Attribute):
                parts.insert(0, value.attr)
                value = value.value
            if isinstance(value, ast.Name) and value.id in imported:
                references.append((node.lineno, ".".join([imported[value.id], *parts])))

        for line, reference in references:
            location = f"{path}:{line}: {reference}"
            parts = reference.split(".")
            assert not {"settings", "model_validator"}.intersection(parts), location
            if reference == "shutil.which":
                assert module in {"app.shell", "app.env"}, (
                    f"{location}: executable lookup outside the execution or host boundary"
                )
            if reference in {"subprocess.run", "subprocess.Popen", "os.system", "os.popen"}:
                assert module == "app.shell", f"{location}: process outside shell boundary"
            if reference == "builtins.print" or (
                reference.startswith("rich.") and parts[-1] in {"Console", "print", "print_json"}
            ):
                assert module == "app.reporting", f"{location}: output outside reporting"
            if not reference.startswith("app."):
                continue
            assert not any(part.startswith("_") and not part.startswith("__") for part in parts), (
                location
            )
            dependency = max(
                (name for name in modules if reference == name or reference.startswith(name + ".")),
                key=len,
            )
            assert dependency in allowed[module], f"{location} is outside {module}'s boundary"
