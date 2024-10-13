"""Miscellaneous utility functions."""

__all__ = [
    "WINDOWS",
    "MACOS",
    "LINUX",
    "UNIX",
    "ARM",
    "PLATFORM",
    "InternalArg",
    "post_install_tasks",
    "post_installation",
    "load_env",
    "create_plugin",
    # "cli_selector",
]

import inspect
import platform
import sys
from functools import partial
from pathlib import Path
from typing import Any, Callable, Optional

import typer
from dotenv import dotenv_values

from app.models import PluginProtocol

from .filesystem import create_temp_file
from .logging import LOGGER
from .shell import Executable, Shell

# from rich.console import Console
# from rich.table import Table


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
PLATFORM = platform.platform().replace("-", "[black]|[/]")

InternalArg = typer.Option(parser=lambda _: _, hidden=True, expose_value=False)
"""An internal argument that is not exposed in the CLI."""

post_install_tasks: list[Callable[[], None]] = []
"""Post installation tasks."""


def post_installation(*_: Any, **__: Any) -> None:
    """Run post installation tasks."""
    for task in post_install_tasks:
        task()


def load_env(env: Path) -> dict[str, Optional[str]]:
    """Load environment variables from a file."""
    LOGGER.debug("Loaded environment variables from: %s", env)
    path = create_temp_file(env.name)
    shell = Shell()

    if UNIX and env.suffix in (".ps1", ".psm1"):
        shell.executable = Executable.PWSH
        cmd = (
            f'. "{env}" ; Get-ChildItem Env:* | ForEach-Object '
            f'{{ "$($_.Name)=$($_.Value)" }} | Out-File -FilePath "{path}"'
        )
        shell.executable = Executable.PWSH
    else:
        cmd = f"source '{env}' && env > '{path}'"
    shell.execute(cmd)

    # filter out unparsable environment variables
    def _filter(lines: list[str]) -> list[str]:
        lines = [line for line in lines if "=" in line]
        lines = [line for line in lines if not line.startswith("_=")]
        return lines

    # update the file in place
    with open(path, "r+", encoding="utf-8") as file:
        file.seek(0)
        file.writelines(_filter(file.readlines()))
        file.truncate()
    return dotenv_values(path)


def create_plugin(plugin: PluginProtocol, *partials: partial[Any]) -> typer.Typer:
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


# def cli_selector(options: list[str], title: str) -> str:
#     """Select an option from a list of options."""
#     console = Console()
#     table = Table(title=title)

#     table.add_column(justify="right", style="green", no_wrap=True)
#     table.add_column(style="magenta")
#     for i, name in enumerate(options):
#         table.add_row(str(i + 1), name)
#     console.print(table)

#     while True:
#         choice = console.input("Choose an environment: ")
#         try:

#             index = int(choice) - 1
#             if 0 <= index < len(options):
#                 return options[index]

#             raise ValueError
#         except ValueError:
#             console.print("[red]Invalid number.[/]")
