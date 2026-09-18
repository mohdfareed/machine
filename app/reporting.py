"""Shared console presentation."""

import os
import sys
from collections.abc import Iterable
from pathlib import Path

import click
import typer
from rich.columns import Columns
from rich.console import Console
from rich.padding import Padding
from rich.text import Text

_console = Console()
_err_console = Console(stderr=True)

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Presentation
# ═════════════════════════════════════════════════════════════════════════════


def heading(message: str) -> None:
    """Start a human-readable section without fixed-width decoration."""
    detail("")
    _print(message, prefix=" ", style="bold blue")


def success(message: str) -> None:
    """Mark a successfully completed operation."""
    _print(message, prefix=" ", style="bold green")
    # _print(message, prefix=" ", style="bold green")


def warning(message: str) -> None:
    """Show a non-fatal problem on the error console."""
    # _print(message, prefix=" ", style="bold yellow", error=True)
    _print(message, prefix=" ", style="bold yellow", error=True)


def error(message: str) -> None:
    """Show a short failure summary on the error console."""
    # _print(message, prefix=" ", style="bold red", error=True)
    _print(message, prefix=" ", style="bold red", error=True)


def command(cmd: str, *, root: Path | None = None) -> None:
    """Announce a command with common roots abbreviated."""
    display = _display_text(cmd, root=root)
    _print(display, prefix=" ", style="magenta")
    if display != cmd:
        debug(f"Exec: {cmd}")


def command_end(code: int) -> None:
    """Announce a command exit."""
    _print(f"=> {code}", prefix="# ", style="magenta")


def detail(message: str | Text, *, error: bool = False) -> None:
    """Show secondary information or recovery guidance."""
    _print(message, prefix="  ", style="dim", error=error)


def debug(message: str) -> None:
    """Show diagnostic context when the active CLI invocation enables debugging."""
    context = click.get_current_context(silent=True)
    if context is None or not getattr(context.find_root().obj, "debug", False):
        return
    _print(message, prefix=" ", style="dim")


def plain(message: str, *, error: bool = False, end: str = "\n") -> None:
    """Print literal text without styling or wrapping, with the requested ending."""
    print(message, file=sys.stderr if error else sys.stdout, end=end)


# Special Functions
# ─────────────────────────────────────────────────────────────────────────────


def path(value: Path, *, root: Path | None = None, prefix: str = "") -> None:
    """Show a prefixed path with its final component emphasized and common roots abbreviated."""
    text = Text(prefix, style="dim")
    text.append_text(_path_text(value, root=root))
    detail(text)


def link(source: Path, target: Path, *, root: Path | None = None) -> None:
    """Show a source-to-target file mapping with common roots abbreviated."""
    detail(_path_text(source, root=root))

    target_text = Text("╰─▶ ", style="dim")
    target_text.append_text(_path_text(target, root=root))
    detail(target_text)


def exception(debug: bool) -> None:
    """Show the current exception traceback on the error console."""
    _err_console.print_exception(show_locals=debug)


def prompt(message: str, choices: list[str]) -> str:
    """Prompt for one of the allowed values, accepting any casing."""
    # return typer.prompt(f"? {message}", type=click.Choice(choices, case_sensitive=False))
    return typer.prompt(f" {message}", type=click.Choice(choices, case_sensitive=False))


def grid(values: Iterable[str], *, left: int = 2) -> None:
    """Show values in adaptive, unboxed columns with optional left padding."""
    _console.print(
        Padding(
            Columns(
                [Text(value, style="dim") for value in values],
                padding=(0, 2),
                column_first=False,
            ),
            (0, 0, 0, left),
        )
    )


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Rendering Helpers
# ═════════════════════════════════════════════════════════════════════════════


def _print(
    message: str | Text,
    *,
    prefix: str = "",
    style: str = "",
    error: bool = False,
) -> None:
    output = _err_console if error else _console
    if not isinstance(message, Text):
        output.print(Text(prefix + message, style=style))
        return

    text = Text(prefix, style=style)
    text.append_text(message)
    output.print(text)


def _display_text(value: str, *, root: Path | None = None) -> str:
    if root is not None:
        value = value.replace(str(root) + os.sep, "$MC_HOME" + os.sep)
    return value.replace(str(Path.home()) + os.sep, "~" + os.sep)


def _path_text(value: Path, *, root: Path | None = None) -> Text:
    path = value
    if root is not None and path.is_relative_to(root):
        path = Path("$MC_HOME") / path.relative_to(root)
    elif path.is_relative_to(Path.home()):
        path = Path("~") / path.relative_to(Path.home())

    name = path.name
    return Text(str(path).removesuffix(name), style="dim") + Text(name, style="bold underline")
