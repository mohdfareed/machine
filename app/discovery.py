"""Discover machines, modules, and their scripts."""

from pathlib import Path

SCRIPT_SUFFIXES = {".sh", ".py", ".ps1"}
"""Set of valid script file extensions."""


# =============================================================================
# MARK: Machines and Modules
# =============================================================================


def list_modules(root: Path) -> list[str]:
    """List available module names by scanning ``config/``."""
    modules_dir = root / "config"
    if not modules_dir.exists():
        return []

    # Traverse grouping folders, stopping at each module directory.
    names: set[str] = set()
    for directory, dirs, files in modules_dir.walk():
        if directory == modules_dir or "module.py" not in files:
            dirs[:] = [name for name in dirs if not name.startswith(".") and name != "__pycache__"]
            continue

        parts = directory.relative_to(modules_dir).parts
        if any("." in part for part in parts):
            raise ValueError(f"Module directory names cannot contain dots: {directory}")

        names.add(".".join(parts))
        dirs.clear()

    return sorted(names)


def list_machines(root: Path) -> list[str]:
    """List available machine IDs by scanning ``machines/``."""
    machines_dir = root / "machines"
    if not machines_dir.exists():
        return []

    names: set[str] = set()
    for entry in machines_dir.iterdir():
        if entry.is_dir() and (entry / "manifest.py").exists():
            names.add(entry.name)

    return sorted(names)


# =============================================================================
# MARK: Scripts
# =============================================================================


def list_scripts(directory: Path) -> list[str]:
    """List supported script files directly inside a directory in sorted order."""
    if not directory.is_dir():
        return []

    return [
        str(script)
        for script in sorted(directory.iterdir())
        if script.is_file() and script.suffix in SCRIPT_SUFFIXES
    ]
