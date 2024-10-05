"""App utilities."""

import logging
import sys
from pathlib import Path

import typer

LOGGER = logging.getLogger("")
"""App logger."""

WINDOWS = "win" in sys.platform
"""Whether the current platform is Windows."""
MACOS = sys.platform == "darwin"
"""Whether the current platform is macOS."""
LINUX = "linux" in sys.platform
"""Whether the current platform is Linux."""
ARM = "arm" in sys.platform
"""Whether the current platform is ARM-based."""


def validate_path(path: Path) -> Path:
    """Validate that a path is valid."""
    if path.exists():
        return path
    raise typer.BadParameter("Path does not exist")


def validate_dir(path: Path) -> Path:
    """Validate that a path is valid."""
    if path.is_dir():
        return path
    raise typer.BadParameter("Path is not a directory")


def validate_file(path: Path) -> Path:
    """Validate that a path is valid."""
    if path.is_file():
        return path
    raise typer.BadParameter("Path is not a directory")


def link(source: Path, target: Path) -> None:
    """Link files and directories from source to target."""
    if target.exists():
        target.unlink()
        LOGGER.debug("Unlinked: %s", target)

    if source.is_dir():
        target.symlink_to(source, target_is_directory=True)
        LOGGER.debug("Linked: %s", source)
        return

    target.symlink_to(source)
    LOGGER.debug("Linked: %s", source)
