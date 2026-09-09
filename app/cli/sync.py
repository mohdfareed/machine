"""Sync canonical repository changes and apply the current machine."""

import logging
import subprocess

import typer

from app.cli.apply import apply
from app.cli.entry import get_current_machine
from app.env import settings
from app.logging import console, err_console

_logger = logging.getLogger(__name__)
_CANONICAL_REPO_URL = "https://github.com/mohdfareed/machine.git"

# =============================================================================
# MARK: Sync Command
# =============================================================================


def sync(
    no_apply: bool = typer.Option(False, "--no-apply", help="Skip apply after sync."),
) -> None:
    """Sync repo changes and re-run apply."""
    if settings.dry_run:
        console.print(f"[dim](dry-run)[/] Fetch main from {_CANONICAL_REPO_URL}")
        return

    # Fetch and merge canonical main in the repo root.
    git = ["git", "-C", str(settings.home)]
    for args in (
        ["fetch", "--no-tags", _CANONICAL_REPO_URL, "refs/heads/main"],
        ["merge", "--ff-only", "--autostash", "FETCH_HEAD"],
    ):
        result = subprocess.run([*git, *args], capture_output=True, text=True)
        if result.returncode != 0:
            _logger.error("git %s failed:\n%s\n%s", " ".join(args), result.stdout, result.stderr)
            err_console.print("[red]Git sync failed.[/]")
            err_console.print(f"[dim]See {settings.log_file} for details.[/]")
            err_console.print("[dim]Resolve the Git error, then run: mc sync[/]")
            raise SystemExit(1)

    # Check for conflicts left by autostash restoration.
    # Autostash conflicts can leave the merge's exit code at zero.
    result = subprocess.run([*git, "ls-files", "--unmerged"], capture_output=True, text=True)
    if result.returncode != 0:
        _logger.error("git ls-files failed:\n%s\n%s", result.stdout, result.stderr)
        err_console.print("[red]Could not check for conflicts.[/]")
        err_console.print(f"[dim]See {settings.log_file} for details.[/]")
        err_console.print("[dim]Resolve the Git error, then run: mc sync[/]")
        raise SystemExit(1)

    if result.stdout.strip():
        err_console.print("[red]Could not restore local changes without conflicts.[/]")
        err_console.print("[dim]Resolve conflicts before applying.[/]")
        raise SystemExit(1)

    # Report the sync result and stop if apply was skipped.
    console.print("[green]Synced with canonical main.[/]")
    if no_apply:
        return

    # Deploy the current machine.
    console.print()
    machine_id = get_current_machine()
    apply(machine=machine_id)
