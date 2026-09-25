"""Discover machines, modules, and their scripts."""

from keyword import iskeyword
from pathlib import Path

from app import env

SCRIPT_SUFFIXES = {".sh", ".py", ".ps1"}
"""Set of valid script file extensions."""


def list_scripts(directory: Path) -> list[Path]:
    """List supported script files directly inside a directory in sorted order."""
    if not directory.is_dir():
        return []

    return [
        script
        for script in sorted(directory.iterdir())
        if script.is_file() and script.suffix.lower() in SCRIPT_SUFFIXES
    ]


def list_modules() -> list[str]:
    """List available module names by scanning ``config/``."""
    root = env.ROOT / "config"
    names: list[str] = []
    for path in root.rglob("module.py"):
        parts = path.parent.relative_to(root).parts

        # Validation.
        if not parts or not path.is_file():
            continue  # Not a module.
        if any(part.startswith(".") or part == "__pycache__" for part in parts):
            continue  # Skip hidden or cache directories.
        if any(not part.isidentifier() or iskeyword(part) for part in parts):
            raise ValueError(f"Module directory names must be Python identifiers: {path.parent}")

        names.append(".".join(parts))
    return sorted(names)


def list_machines() -> list[str]:
    """List available machine IDs by scanning ``machines/``."""
    machines_dir = env.ROOT / "machines"
    if not machines_dir.exists():
        return []

    names: set[str] = set()
    for entry in machines_dir.iterdir():
        if entry.is_dir() and (entry / "machine.py").exists():
            names.add(entry.name)

    return sorted(names)
