"""Miscellaneous utility functions."""

__all__ = [
    "WINDOWS",
    "MACOS",
    "LINUX",
    "UNIX",
    "ARM",
    "InternalArg",
    "post_install_tasks",
    "post_installation",
    "with_status",
    "install_with_progress",
    "install_from_specs",
    "create_plugin",
    "cli_selector",
]

import inspect
import platform
import sys
from functools import partial, wraps
from typing import TYPE_CHECKING, Any, Callable, TypeVar

import rich
import rich.progress
import rich.status
import typer
from rich.console import Console
from rich.table import Table

from .logging import LOGGER

# typechecking imports
if TYPE_CHECKING:
    from app import models

T = TypeVar("T")


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

InternalArg = typer.Option(parser=lambda _: _, hidden=True, expose_value=False)
"""An internal argument that is not exposed in the CLI."""

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


def install_with_progress(
    message: str,
) -> Callable[[Callable[[Any, str], None]], Callable[[Any, str], None]]:
    """Decorator to show a progress bar while running a function."""

    def decorator(func: Callable[[Any, str], None]) -> Callable[[Any, str], None]:
        @wraps(func)
        def wrapper(self: Any, iterable: str, *args: Any, **kwargs: Any) -> None:
            items = iterable.split()

            for i in rich.progress.track(
                range(len(items)), description=f"{message}...", transient=True
            ):
                LOGGER.info("Installing %s using %s...", items[i], self.name)
                func(self, items[i], *args, **kwargs)
                LOGGER.debug("%s was installed successfully.", items[i])

        return wrapper

    return decorator


def install_from_specs(specs: list["models.PackageSpec"]) -> None:
    """Install packages from a specification."""
    for spec in specs:
        manager = spec[0]
        installer = spec[1]

        if manager.is_supported():
            installer()
            return

    LOGGER.error("No supported package manager found.")
    raise typer.Abort


def create_plugin(
    plugin: "models.PluginProtocol", *partials: partial[Any]
) -> typer.Typer:
    """Create a plugin from a list of partials. The first partial is the plugin module."""
    app_clone = typer.Typer()
    plugin_app = plugin.plugin_app

    # Clone the plugin app and info
    app_clone.info = plugin_app.info
    app_clone.registered_callback = plugin_app.registered_callback
    app_clone.registered_commands = plugin_app.registered_commands
    app_clone.registered_groups = plugin_app.registered_groups

    # Register partial functions as commands to the plugin app
    for partial_func in partials:
        app_clone.command()(_apply_partial(partial_func))
    return app_clone


def _apply_partial(partial_func: partial[Any]) -> Any:

    # Get the signature of the function and the arguments
    signature = inspect.signature(partial_func.func)
    args = iter(partial_func.args)
    kwargs = partial_func.keywords

    # Create the new defaults for the function
    new_defaults: list[Any] = []
    for name, param in signature.parameters.items():

        # Positional -> Keyword -> Default -> None
        new_defaults.append(next(args, kwargs.pop(name, param.default)))
        if new_defaults[-1] == inspect.Parameter.empty:
            new_defaults.pop()

    # Update the function with the new defaults
    partial_func.func.__defaults__ = tuple(new_defaults)
    return partial_func.func


def cli_selector(options: list[str], title: str) -> str:
    """Select an option from a list of options."""
    console = Console()
    table = Table(title=title)

    table.add_column(justify="right", style="green", no_wrap=True)
    table.add_column(style="magenta")
    for i, name in enumerate(options):
        table.add_row(str(i + 1), name)
    console.print(table)

    while True:
        choice = console.input("Choose an option: ")
        try:

            index = int(choice) - 1
            if 0 <= index < len(options):
                return options[index]

            raise ValueError
        except ValueError:
            console.print("[red]Invalid number.[/]")
