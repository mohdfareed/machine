"""Keep direct process execution behind the shared preview and environment boundary."""

import ast
from pathlib import Path


def test_subprocesses_use_shell_boundary() -> None:
    root = Path(__file__).parents[1] / "app"
    commands = {"subprocess": {"run", "Popen"}, "os": {"system", "popen"}}
    for path in root.rglob("*.py"):
        if path == root / "runtime" / "shell.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            owner = node.func.value
            if isinstance(owner, ast.Name):
                assert node.func.attr not in commands.get(owner.id, set()), path
