"""Shared console presentation and plain-text outcome logging."""

import logging
from pathlib import Path

import typer
from rich.text import Text

from app.env import settings
from app.logging import console, err_console
from app.models import Failure

_logger = logging.getLogger(__name__)


# =============================================================================
# MARK: Presentation
# =============================================================================


def _print(
    message: str,
    *,
    prefix: str = "",
    style: str = "",
    error: bool = False,
    level: int = logging.INFO,
    space: bool = False,
) -> None:
    output = err_console if error else console
    if space:
        output.print()
    output.print(Text(prefix + message, style=style))
    _logger.log(level, message, extra={"reported": True})


def heading(message: str) -> None:
    """Start a human-readable section without fixed-width decoration."""
    _print(message, prefix="▶ ", style="bold magenta", space=True)


def detail(message: str, *, error: bool = False) -> None:
    """Show secondary information or recovery guidance."""
    _print(message, prefix="  ", style="dim", error=error)


def success(message: str) -> None:
    """Mark a successfully completed operation."""
    _print(message, prefix="✓ ", style="green", space=True)


def warning(message: str) -> None:
    """Show a non-fatal problem on the error console."""
    _print(message, prefix="! ", style="yellow", error=True, level=logging.WARNING)


def error(message: str) -> None:
    """Show a short failure summary on the error console."""
    _print(message, prefix="✗ ", style="red", error=True, level=logging.ERROR, space=True)


def command(cmd: str) -> None:
    """Announce a command without altering its external output."""
    label = "Would run: " if settings.dry_run else "$ "
    _print(label + cmd, prefix="  ", style="dim")
    if not settings.dry_run:
        console.print()


# =============================================================================
# MARK: Summary
# =============================================================================


def print_summary(
    failures: list[Failure],
    log_file: Path,
    *,
    init_failed: bool = False,
) -> None:
    """Report the outcome and exit unsuccessfully when operations failed."""
    if not failures:
        message = "Plan complete." if settings.dry_run else "Complete."
        success(message)
        detail(f"Log: {log_file}")
        return

    error(f"Finished with {len(failures)} failure(s).")
    for failure in failures:
        detail(f"Failed: {failure.module} · {failure.item}", error=True)
    if init_failed:
        detail("Initialization failed; remaining steps were not run.", error=True)
    detail(f"Log: {log_file}", error=True)
    raise typer.Exit(1)
