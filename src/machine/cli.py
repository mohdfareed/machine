"""Machine CLI application."""

import logging
import subprocess
import sys
from pathlib import Path

import typer
from rich.table import Table

from machine.core import (
    console,
    err_console,
    settings,
    setup_console_logging,
    setup_file_logging,
)

app = typer.Typer(
    help=settings.description,
    no_args_is_help=True,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

_logger = logging.getLogger(__name__)


def main(prog_name: str | None = None) -> None:
    """Entry point."""
    try:
        app(prog_name=prog_name)
    except Exception as e:
        if settings.debug:
            _logger.error("An error occurred: %s", e, exc_info=True)
        else:
            err_console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)


# MARK: Completion Callbacks


def _complete_machines(incomplete: str) -> list[tuple[str, str]]:
    from machine.manifest import list_machines

    return [
        (n, "Machine") for n in list_machines(settings.home) if n.startswith(incomplete)
    ]


# MARK: Global Options


@app.callback()
def callback(
    debug: bool = typer.Option(False, "-d", "--debug", help="Enable debug logging."),
    dry_run: bool = typer.Option(
        False, "-n", "--dry-run", help="Preview changes without applying."
    ),
    version: bool = typer.Option(
        False, "-v", "--version", help="Show version and exit."
    ),
) -> None:
    settings.debug = debug
    settings.dry_run = dry_run
    setup_console_logging()
    setup_file_logging()

    if version:
        console.print(f"{settings.name} {settings.version}")
        sys.exit(0)


# MARK: Lifecycle Commands


@app.command(rich_help_panel="Lifecycle")
def setup(
    machine_id: str = typer.Argument(
        help="Machine to set up.",
        autocompletion=_complete_machines,
    ),
) -> None:
    """Deploy configs, install packages, and run scripts."""
    from machine.app import deploy_files, install_packages, run_scripts, validate
    from machine.manifest import load_manifest, load_module

    root = settings.home
    manifest = load_manifest(machine_id, root)
    modules = [
        load_module(m, root) if isinstance(m, str) else m for m in manifest.modules
    ]

    # Fail fast on misconfiguration
    errors = validate(modules, manifest.env, machine_id)
    if errors:
        for e in errors:
            err_console.print(f"[red]  {e}[/]")
        raise SystemExit(1)

    mode = "[dim](dry-run)[/] " if settings.dry_run else ""
    console.print(f"{mode}Setting up [bold]{machine_id}[/]")
    if modules:
        console.print(f"  Modules: {', '.join(m.name for m in modules)}")

    all_files = [f for m in modules for f in m.files] + manifest.files
    all_packages = [p for m in modules for p in m.packages] + manifest.packages
    all_scripts = [s for m in modules for s in m.scripts] + manifest.scripts

    # Env injected into every script subprocess — never written to disk
    script_env = {"MC_HOME": str(root), "MC_ID": machine_id, **manifest.env}

    count = deploy_files(all_files)
    console.print(f"  Files: {count} created/updated")

    # Two-phase script execution: setup scripts prepare the environment
    # (package managers, OS features) before packages are installed.
    setup = [s for s in all_scripts if Path(s).name.startswith("setup")]
    post = [s for s in all_scripts if not Path(s).name.startswith("setup")]

    run_scripts(setup, env=script_env)
    install_packages(all_packages)
    run_scripts(post, env=script_env)

    console.print("[bold green]Done![/]")


@app.command(rich_help_panel="Lifecycle")
def update(
    stash: bool = typer.Option(
        False, "-s", "--stash", help="Stash and reapply local changes."
    ),
) -> None:
    """Update the CLI tool."""
    root = settings.home
    git = ["git", "-C", str(root)]

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


# MARK: Info Commands


@app.command("list", rich_help_panel="Info")
def list_all() -> None:
    """List available machines and modules."""
    from machine.manifest import list_machines, list_modules

    root = settings.home
    machines = list_machines(root)
    modules = list_modules(root)

    if machines:
        console.print("[bold]Machines:[/]")
        for name in machines:
            console.print(f"  {name}")
    else:
        console.print("[dim]No machines found[/]")

    if modules:
        console.print("[bold]Modules:[/]")
        for name in modules:
            console.print(f"  {name}")
    else:
        console.print("[dim]No modules found[/]")


@app.command(rich_help_panel="Info")
def show(
    machine_id: str = typer.Argument(
        help="Machine to inspect.",
        autocompletion=_complete_machines,
    ),
) -> None:
    """Show resolved configuration for a machine."""
    from machine.manifest import load_manifest, load_module

    root = settings.home
    manifest = load_manifest(machine_id, root)
    modules = [
        load_module(m, root) if isinstance(m, str) else m for m in manifest.modules
    ]

    console.print(f"[bold]{machine_id}[/]")
    if modules:
        console.print(f"\n[bold]Modules:[/] {', '.join(m.name for m in modules)}")

    # Show only manifest env (MC_HOME/MC_ID are runtime, not config)
    if manifest.env:
        console.print("\n[bold]Environment:[/]")
        for k, v in manifest.env.items():
            console.print(f"  {k}={v}")

    all_files = [f for m in modules for f in m.files] + manifest.files
    if all_files:
        table = Table(title="Files", show_header=True)
        table.add_column("Source", style="dim")
        table.add_column("Target")
        for f in all_files:
            table.add_row(f.source, f.target)
        console.print()
        console.print(table)

    all_packages = [p for m in modules for p in m.packages] + manifest.packages
    if all_packages:
        table = Table(title="Packages", show_header=True)
        table.add_column("Name")
        table.add_column("Source", style="dim")
        for p in all_packages:
            sources = []
            if p.brew:
                sources.append(f"brew: {p.brew}")
            if p.apt:
                sources.append(f"apt: {p.apt}")
            if p.snap:
                sources.append(f"snap: {p.snap}")
            if p.winget:
                sources.append(f"winget: {p.winget}")
            if p.scoop:
                sources.append(f"scoop: {p.scoop}")
            if p.mas is not None:
                sources.append(f"mas: {p.mas}")
            if p.script:
                sources.append("script")
            table.add_row(p.name, ", ".join(sources))
        console.print()
        console.print(table)

    all_scripts = [s for m in modules for s in m.scripts] + manifest.scripts
    if all_scripts:
        console.print("\n[bold]Scripts:[/]")
        for s in all_scripts:
            console.print(f"  {s}")


@app.command(rich_help_panel="Info")
def info() -> None:
    """Show machine home, app directory, and version."""
    console.print(f"[bold]{settings.name}[/] {settings.version}")
    console.print(f"  Home:  {settings.home}")
    console.print(f"  Data:  {settings.app_dir}")
    console.print(f"  Logs:  {settings.app_dir / 'mc.log'}")
    console.print(f"  State: {settings.app_dir / 'state.json'}")
