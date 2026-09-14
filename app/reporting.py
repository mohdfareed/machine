"""Shared console presentation."""

import sys

import click
import typer
from rich.console import Console
from rich.text import Text

# =============================================================================
# MARK: Presentation
# =============================================================================


def plain(message: str, *, error: bool = False, end: str = "\n") -> None:
    """Print literal text without styling or wrapping, with the requested ending."""
    print(message, file=sys.stderr if error else sys.stdout, end=end)


def prompt(message: str, choices: list[str]) -> str:
    """Prompt for one of the allowed values, accepting any casing."""
    return typer.prompt(message, type=click.Choice(choices, case_sensitive=False))


def exception() -> None:
    """Show the current exception traceback on the error console."""
    _err_console.print_exception()


def detail(message: str, *, error: bool = False) -> None:
    """Show secondary information or recovery guidance."""
    _print(message, prefix="  ", style="dim", error=error)


def success(message: str) -> None:
    """Mark a successfully completed operation."""
    _print(message, prefix="✓ ", style="green")


def warning(message: str) -> None:
    """Show a non-fatal problem on the error console."""
    _print(message, prefix="! ", style="yellow", error=True)


def error(message: str) -> None:
    """Show a short failure summary on the error console."""
    _print(message, prefix="✗ ", style="red", error=True)


def command(cmd: str) -> None:
    """Announce a command without altering its external output."""
    _print("$ " + cmd, prefix="  ", style="dim")


def heading(message: str) -> None:
    """Start a human-readable section without fixed-width decoration."""
    detail("")
    _print(message, prefix="▶ ", style="bold magenta")


# =============================================================================
# MARK: Rendering Helpers
# =============================================================================

_console = Console()
_err_console = Console(stderr=True)


def _print(
    message: str,
    *,
    prefix: str = "",
    style: str = "",
    error: bool = False,
) -> None:
    output = _err_console if error else _console
    output.print(Text(prefix + message, style=style))
