"""Miscellaneous utility functions."""

__all__ = [
    "ARM",
    "WINDOWS",
    "MACOS",
    "LINUX",
    "UNIX",
    "post_install_tasks",
    "post_installation",
    "hidden",
    "is_hidden",
    "with_status",
    "with_progress",
]

import platform
import sys
from functools import wraps
from typing import Any, Callable, TypeVar

import rich
import rich.progress
import rich.status
from rich.console import Console

from app import utils

ARM = platform.machine().startswith(("arm", "aarch"))
"""Whether the current platform is ARM-based."""
WINDOWS = sys.platform.startswith("win")
"""Whether the current platform is Windows."""
LINUX = sys.platform.startswith("linux")
"""Whether the current platform is Linux."""
MACOS = sys.platform.startswith("darwin")
"""Whether the current platform is macOS."""
UNIX = MACOS or LINUX
"""Whether the current platform is Unix-based."""

CLI_HIDE_KEY = "__cli_command__"
"""Key to flag a function as hidden from the CLI app."""

C = TypeVar("C", bound=Callable[..., Any])

post_install_tasks: list[Callable[[], None]] = []
"""Post installation tasks."""


def post_installation(*_: Any, **__: Any) -> None:
    """Run post installation tasks."""
    for task in post_install_tasks:
        task()


def hidden(func: C) -> C:
    """Decorator to hide a function from the CLI app."""
    setattr(func, CLI_HIDE_KEY, True)
    return func


def is_hidden(func: Callable[..., Any]) -> bool:
    """Check if a function is hidden from the CLI app."""
    return getattr(func, CLI_HIDE_KEY, False)


def with_status(msg: str) -> Callable[..., Any]:
    """Decorator to show a status message while running a function."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            utils.LOGGER.info("%s...", msg)
            with Console().status(f"{msg}..."):
                return func(*args, **kwargs)
            utils.LOGGER.debug("Completed successfully.")

        return wrapper

    return decorator


def with_progress(msg: str) -> Callable[..., Any]:
    """Decorator to show a progress bar while running a function."""

    def decorator(func: Callable[[list[Any]], Any]) -> Callable[[list[Any]], Any]:

        @wraps(func)
        def wrapper(items: list[Any]) -> None:
            utils.LOGGER.info("%s...", msg)
            for i in rich.progress.track(
                range(len(items)), description=f"{msg}...", transient=True
            ):
                utils.LOGGER.info("%s %s...", msg, items[i])
                func([items[i]])
                utils.LOGGER.debug("Completed %s successfully.", items[i])
            utils.LOGGER.debug("Completed.")

        return wrapper

    return decorator
