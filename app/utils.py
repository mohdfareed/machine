"""App utilities."""

import logging
import platform
import sys
from pathlib import Path
from typing import Any, Callable, TypeVar

import typer

T = TypeVar("T")

LOGGER = logging.getLogger("")
"""App logger."""

WINDOWS = "win" in sys.platform[:3]
"""Whether the current platform is Windows."""
MACOS = sys.platform == "darwin"
"""Whether the current platform is macOS."""
LINUX = "linux" in sys.platform[:5]
"""Whether the current platform is Linux."""
UNIX = MACOS or LINUX
"""Whether the current platform is Unix-based."""
ARM = platform.machine().startswith(("arm", "aarch64"))
"""Whether the current platform is ARM-based."""

IgnoredArgument = typer.Option(parser=lambda _: _, hidden=True, expose_value=False)
"""An ignored CLI command argument."""
post_install_tasks: list[Callable[[], None]] = []
"""Post installation tasks."""


def post_installation(*_: Any, **__: Any) -> None:
    """Run post installation tasks."""

    LOGGER.info("[bold green]Running post installation tasks...[/]")
    LOGGER.debug("Results: %s", _)
    LOGGER.debug("Options: %s", __)

    for post_install_task in post_install_tasks:
        post_install_task()


def link(source: Path, target: Path) -> None:
    """Link files and directories from source to target."""

    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    target.symlink_to(source, target_is_directory=source.is_dir())


def validate(*validators: Callable[[T], T]) -> Callable[[T], T]:
    """Validate data against a list of validators."""

    def validator(data: T) -> T:
        for _validator in validators:
            data = _validator(data)
        return data

    return validator


def exists(path: Path) -> Path:
    """Validate that a path exists."""
    if path.exists():
        return path
    raise typer.BadParameter(f"Path does not exist: {path}")


def is_dir(path: Path) -> Path:
    """Validate that a path exists and is a directory."""
    if path.exists() and path.is_dir():
        return path
    raise typer.BadParameter(f"Path is not a directory: {path}")


def is_file(path: Path) -> Path:
    """Validate that a path exists and is a file."""
    if path.exists() and path.is_file():
        return path
    raise typer.BadParameter(f"Path is not a file: {path}")
