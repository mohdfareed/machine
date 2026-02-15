"""Machine CLI application."""

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console

from machine.config import app_settings

from .helpers import format_config

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    help=app_settings.description,
    no_args_is_help=True,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def main(prog_name: str | None = None) -> None:
    """Entry point."""
    try:
        app(prog_name=prog_name)
    except Exception as e:
        if app_settings.debug:
            app_settings.logger.error(f"An error occurred: {e}", exc_info=True)
        else:
            err_console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)


@app.callback()
def callback(
    debug: bool = typer.Option(
        app_settings.debug, "-d", "--debug", help="Enable debug logging."
    ),
    dry_run: bool = typer.Option(
        False, "-n", "--dry-run", help="Preview changes without applying."
    ),
    home: Path | None = typer.Option(
        None, "-r", "--root", help="Override home directory."
    ),
    # Meta options
    settings: bool = typer.Option(
        False, "-s", "--settings", help="Show settings overrides and exit."
    ),
    full_settings: bool = typer.Option(
        False, "-S", "--all-settings", help="Show all settings and exit."
    ),
    version: bool = typer.Option(
        False, "-v", "--version", help="Show version and exit."
    ),
) -> None:
    from .helpers import setup_console_logging

    app_settings.debug = debug
    app_settings.dry_run = dry_run
    if home is not None:
        app_settings.home = home.expanduser().resolve()
    setup_console_logging()

    if version:
        console.print(f"{app_settings.name} {app_settings.version}")
        sys.exit(0)

    if settings:
        for line in format_config(app_settings.dump(full=False)):
            console.print(line)
        sys.exit(0)

    if full_settings:
        for line in format_config(app_settings.dump(full=True)):
            console.print(line)
        sys.exit(0)


# MARK: Commands


@app.command()
def setup(
    machine_id: str = typer.Argument(help="Machine to set up."),
) -> None:
    """Deploy configs, install packages, and run scripts."""
    from machine.dotfiles import deploy_dotfiles, write_env
    from machine.manifest import load_manifest
    from machine.packages import install_packages
    from machine.scripts import run_scripts

    root = app_settings.home
    manifest = load_manifest(machine_id, root)

    mode = "[dim](dry-run)[/] " if app_settings.dry_run else ""
    console.print(f"{mode}Setting up [bold]{machine_id}[/]")

    # Write machine env file
    write_env(machine_id, root)

    # Symlink configs
    count = deploy_dotfiles(manifest.dotfiles, root)
    console.print(f"  Dotfiles: {count} created/updated")

    # Install packages
    install_packages(manifest.packages)

    # Run shared scripts, then machine scripts
    run_scripts(root / "config" / "scripts")
    run_scripts(root / "machines" / machine_id / "scripts")

    console.print("[bold green]Done![/]")


@app.command("list")
def list_machines() -> None:
    """List available machines."""
    machines_dir = app_settings.home / "machines"
    if not machines_dir.exists():
        console.print("No machines directory found")
        return

    for d in sorted(machines_dir.iterdir()):
        if d.is_dir() and (d / "manifest.py").exists():
            console.print(f"  {d.name}")


@app.command()
def update(
    stash: bool = typer.Option(
        False, "-s", "--stash", help="Stash and reapply local changes."
    ),
) -> None:
    """Update the CLI tool."""
    root = app_settings.home
    git = ["git", "-C", str(root)]

    # Check if dirty
    result = subprocess.run(
        [*git, "status", "--porcelain"], capture_output=True, text=True
    )
    is_dirty = bool(result.stdout.strip())

    if is_dirty:
        if not stash:
            console.print(
                "[red]Update failed: local changes. Use --stash to auto-stash.[/]"
            )
            raise SystemExit(1)

        subprocess.run([*git, "stash", "push", "-m", "mc update"])
        console.print("[yellow]Stashed local changes.[/]")

    result = subprocess.run([*git, "pull", "--ff-only"], capture_output=True, text=True)
    if result.returncode != 0:
        console.print("[red]Update failed.[/]")
        raise SystemExit(1)

    console.print("[green]Updated.[/]")
    if is_dirty and stash:
        subprocess.run([*git, "stash", "pop"])


@app.command()
def home() -> None:
    """Print machine home directory."""
    console.print(app_settings.home)
