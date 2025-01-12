"""Miscellaneous utility functions."""

__all__ = [
    "ARM",
    "WINDOWS",
    "MACOS",
    "LINUX",
    "UNIX",
    "post_install_tasks",
    "post_installation",
    "with_status",
    "with_progress",
]

import platform
import sys
from functools import wraps
from typing import Any, Callable

import rich
import rich.progress
import rich.status
from rich.console import Console

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

_InstallFunc = Callable[[Any, list[Any], Any, Any], Any]

post_install_tasks: list[Callable[[], None]] = []
"""Post installation tasks."""


def post_installation(*_: Any, **__: Any) -> None:
    """Run post installation tasks."""
    for task in post_install_tasks:
        task()


def with_status(message: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to show a status message while running a function."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with Console().status(message):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def with_progress(
    message: str,
) -> Callable[[Callable[[list[Any]], Any]], Callable[[list[Any]], Any]]:
    """Decorator to show a progress bar while running a function."""

    def decorator(func: Callable[[list[Any]], Any]) -> Callable[[list[Any]], Any]:

        @wraps(func)
        def wrapper(items: list[Any]) -> None:

            for i in rich.progress.track(
                range(len(items)), description=message, transient=True
            ):
                func([items[i]])

        return wrapper

    return decorator
