"""App utilities."""

import logging
import platform
import sys
from pathlib import Path
from typing import Callable, TypeVar

import typer

LOGGER = logging.getLogger("")
"""App logger."""

WINDOWS = "win" in sys.platform[:3]
"""Whether the current platform is Windows."""
MACOS = sys.platform == "darwin"
"""Whether the current platform is macOS."""
LINUX = "linux" in sys.platform[:5]
"""Whether the current platform is Linux."""
ARM = platform.machine().startswith(("arm", "aarch64"))
"""Whether the current platform is ARM-based."""

T = TypeVar("T")

IgnoredArgument = typer.Option(parser=lambda _: _, hidden=True, expose_value=False)


def link(source: Path, target: Path) -> None:
    """Link files and directories from source to target."""

    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    target.symlink_to(source, target_is_directory=source.is_dir())


def validate(*validators: Callable[[T], T]) -> Callable[[T], T]:
    """Validate data against a list of validators."""

    def is_valid(data: T) -> T:
        for validator in validators:
            data = validator(data)
        return data

    return is_valid


def path_exists(path: Path) -> Path:
    """Validate that a path is valid."""

    if path.exists():
        return path
    raise typer.BadParameter(f"Path does not exist: {path}")


def is_dir(path: Path) -> Path:
    """Validate that a path is valid."""

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        return path

    if path.is_dir():
        return path
    raise typer.BadParameter(f"Path is not a directory: {path}")


def is_file(path: Path) -> Path:
    """Validate that a path is valid."""

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return path

    if path.is_file():
        return path
    raise typer.BadParameter(f"Path is not a file: {path}")
