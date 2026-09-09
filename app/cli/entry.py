"""CLI entry point, callbacks, completion, and current-machine selection."""

import logging
import sys
from pathlib import Path

import click
import typer

from app.discovery import list_machines, list_modules
from app.env import settings
from app.logging import (
    console,
    err_console,
    setup_console_logging,
    setup_file_logging,
)
from app.models import Failure

_logger = logging.getLogger(__name__)

# =============================================================================
# MARK: App Entry Point
# =============================================================================


def main(prog_name: str | None = None) -> None:
    """Run the CLI and handle interrupts and unexpected errors."""
    try:
        _create_app()(prog_name=prog_name)

    # Handle user interrupts.
    except KeyboardInterrupt:
        err_console.print("\n[dim]Interrupted.[/]")
        sys.exit(130)

    # Handle unexpected errors.
    except Exception as e:
        _logger.debug("Unhandled exception", exc_info=True)
        err_console.print(f"[red]Error: {e}[/]")
        err_console.print(f"[dim]See {settings.log_file} for details.[/]")
        sys.exit(1)


# =============================================================================
# MARK: Current Machine
# =============================================================================

machines = click.Choice(list_machines(settings.home), case_sensitive=False)


def get_current_machine() -> str | None:
    """Return the last-used machine ID, or None if not set."""
    return settings.machine_file.read_text().strip() if settings.machine_file.exists() else None


def save_current_machine(machine_id: str) -> None:
    """Persist the current machine ID."""
    settings.machine_file.parent.mkdir(parents=True, exist_ok=True)
    settings.machine_file.write_text(machine_id)


# =============================================================================
# MARK: Callbacks
# =============================================================================


def _callback(
    debug: bool = typer.Option(False, "-d", "--debug", help="Enable debug logging."),
    dry_run: bool = typer.Option(
        False, "-n", "--dry-run", help="Preview changes without applying."
    ),
    version: bool = typer.Option(False, "-v", "--version", help="Show version and exit."),
) -> None:

    # Configure runtime options and console logging.
    settings.debug = debug
    settings.dry_run = dry_run
    setup_console_logging()

    # Handle informational exits before initializing file logging.
    if version:
        console.print(f"{settings.name} {settings.version}")
        sys.exit(0)

    if {"-h", "--help"} & set(sys.argv):
        return

    setup_file_logging()


# =============================================================================
# MARK: Helpers
# =============================================================================


def complete_machines(incomplete: str) -> list[tuple[str, str]]:
    """Shell completion for machine IDs, marking the current selection."""
    return [
        (n, "Machine (default)" if n == get_current_machine() else "Machine")
        for n in list_machines(settings.home)
        if n.startswith(incomplete)
    ]


def complete_modules(incomplete: str) -> list[tuple[str, str]]:
    """Shell completion for discovered module names."""
    return [(n, "Module") for n in list_modules(settings.home) if n.startswith(incomplete)]


def print_summary(failures: list[Failure], log_file: Path) -> None:
    """Report deployment results and exit unsuccessfully when failures remain."""
    if not failures:
        console.print(f"\n[bold green]Done![/] [dim](log: {log_file})[/]")
        return

    err_console.print(f"\n[red]Completed with {len(failures)} failure(s):[/]")
    for failure in failures:
        err_console.print(
            f"  [red]\\[{failure.module}][/] {failure.item} [dim]({failure.detail})[/]"
        )
    err_console.print(f"[dim]See {log_file} for details.[/]")

    raise typer.Exit(1)

def _create_app() -> typer.Typer:
    # Load command owners after their shared callbacks and state helpers are available.
    from app.cli import apply, info, sync, update

    # Create the app and attach its callback and status commands.
    app = typer.Typer(
        help=settings.description,
        no_args_is_help=True,
        invoke_without_command=True,
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    app.add_typer(info.status_app, name="status", rich_help_panel="Info")
    app.callback()(_callback)

    # Register lifecycle and info commands in their help panels.
    app.command(rich_help_panel="Lifecycle")(apply.apply)
    app.command(rich_help_panel="Lifecycle")(update.update)
    app.command(rich_help_panel="Lifecycle")(sync.sync)
    app.command(rich_help_panel="Info")(info.home)
    app.command(rich_help_panel="Info")(info.private)
    app.command("list", rich_help_panel="Info")(info.list_all)
    app.command(rich_help_panel="Info")(info.show)
    return app
