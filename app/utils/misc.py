"""Miscellaneous utility functions."""

__all__ = [
    "InternalArg",
    "load_env",
    # "cli_selector",
    "WINDOWS",
    "MACOS",
    "LINUX",
    "UNIX",
    "ARM",
]

import platform
import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import dotenv_values

from .filesystem import create_temp_file
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

InternalArg = typer.Option(parser=lambda _: _, hidden=True, expose_value=False)
"""An internal argument that is not exposed in the CLI."""


def load_env(env: Path) -> dict[str, Optional[str]]:
    """Load environment variables from a file."""

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
