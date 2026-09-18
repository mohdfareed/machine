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
    modules_dir = env.ROOT / "config"
    if not modules_dir.exists():
        return []

    # Traverse grouping folders, stopping at each module directory.
    names: set[str] = set()
    for directory, dirs, files in modules_dir.walk():
        if directory == modules_dir or "module.py" not in files:
            dirs[:] = [name for name in dirs if not name.startswith(".") and name != "__pycache__"]
            # Reject names that collapse to one directory on case-insensitive filesystems.
            by_case: dict[str, str] = {}
            for name in dirs:
                if previous := by_case.get(name.casefold()):
                    raise ValueError(
                        f"Module directory names differ only by case: "
                        f"{directory / previous}, {directory / name}"
                    )
                by_case[name.casefold()] = name
            continue

        parts = directory.relative_to(modules_dir).parts
        if any(not part.isidentifier() or iskeyword(part) for part in parts):
            raise ValueError(f"Module directory names must be Python identifiers: {directory}")

        names.add(".".join(parts))
        dirs.clear()

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
