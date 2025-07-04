"""Miscellaneous utility functions."""

__all__ = [
    "SetupTask",
    "Platform",
    "progress",
    "post_setup",
    "add_post_setup_task",
    "pkg_installer",
    "loading_indicator",
    "hidden",
    "is_hidden",
]

import atexit
import platform
import sys
from enum import Flag
from functools import wraps
from typing import Any, Callable, TypeVar

import rich.progress

from .logging import LOGGER, app_console

CLI_VISIBILITY_KEY = "__cli_command_hidden__"


SetupTask = Callable[[], None]
Command = Callable[..., Any]

C = TypeVar("C", bound=Command)

progress = rich.progress.Progress(transient=True, console=app_console)
post_install_tasks: list[SetupTask] = []
progress.start()
atexit.register(progress.stop)


class Platform(Flag):
    """Platform types."""

    WINDOWS = sys.platform.startswith("win")
    """Windows platform."""
    LINUX = sys.platform.startswith("linux")
    """Linux platform."""
    MACOS = sys.platform.startswith("darwin")
    """macOS platform."""
    UNIX = MACOS or LINUX
    """Unix-based platform."""
    ARM = platform.machine().startswith(("arm", "aarch"))
    """ARM-based platform."""


# MARK: Installation task management


def post_setup(*_: Any, **__: Any) -> None:
    """Run installation tasks."""
    LOGGER.info("Running post setup tasks...")
    post_install = progress.add_task(
        "[green]Post-installation...", total=len(post_install_tasks)
    )

    for task in set(post_install_tasks):
        task_id = progress.add_task(
            f"[green]Running {task.__name__}...", total=None
        )
        task()
        progress.remove_task(task_id)

        progress.update(post_install, advance=1)
    progress.remove_task(post_install)
    LOGGER.info("Post setup tasks completed.")


def add_post_setup_task(task: SetupTask) -> None:
    """Add a task to the post installation tasks."""
    post_install_tasks.append(task)


def pkg_installer(func: Callable[..., None]) -> Callable[..., None]:
    """Decorator to install a package."""

    @wraps(func)
    def install(self: Any, package: str, *args: Any, **kwargs: Any) -> None:
        packages = package.split()

        if len(packages) < 2:
            LOGGER.info("Installing %s...", package)
            task_id = progress.add_task(
                f"[green]Installing {package}...", total=None
            )
            func(self, package, *args, **kwargs)
            progress.remove_task(task_id)
            LOGGER.debug("Installed %s.", package)
            return

        task_id = progress.add_task(
            "[green]Installing packages...", total=len(packages)
        )
        for pkg in packages:
            LOGGER.info("Installing %s...", pkg)
            func(self, package, *args, **kwargs)
            progress.update(task_id, advance=1)
            LOGGER.debug("Installed %s.", pkg)
        progress.remove_task(task_id)

    return install


def loading_indicator(msg: str) -> Callable[..., Callable[..., Any]]:
    """Decorator to show a loading indicator while the function is running."""

    def indicator(func: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            task_id = progress.add_task(f"[green]{msg}...", total=None)
            result = func(*args, **kwargs)
            progress.remove_task(task_id)
            return result

        return wrapper

    return indicator


# MARK: CLI decorators


def hidden(func: C) -> C:
    """Decorator to hide a function from the CLI app."""
    setattr(func, CLI_VISIBILITY_KEY, True)
    return func


def is_hidden(func: Command) -> bool:
    """Check if a function is hidden from the CLI app."""
    return getattr(func, CLI_VISIBILITY_KEY, False)
