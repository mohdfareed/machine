"""Machine CLI application."""

import contextlib
import logging
import os
import subprocess
import sys
from pathlib import Path

import typer
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TaskID, TextColumn
from rich.table import Table

from machine.core import (
    console,
    err_console,
    mute_console_logging,
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

    if version:
        console.print(f"{settings.name} {settings.version}")
        sys.exit(0)

    # Only log to file for real command runs, not help/version
    if not {"-h", "--help"} & set(sys.argv):
        setup_file_logging()


# MARK: Lifecycle Commands


@app.command(rich_help_panel="Lifecycle")
def setup(
    machine_id: str = typer.Argument(
        help="Machine to set up.",
        autocompletion=_complete_machines,
    ),
) -> None:
    """Deploy configs, install packages, and run scripts."""
    from machine.app import (
        deploy_files,
        filter_scripts,
        install_packages,
        run_scripts,
        validate,
    )
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
    all_scripts = filter_scripts(
        [s for m in modules for s in m.scripts] + manifest.scripts
    )

    # Env injected into every script subprocess — never written to disk.
    # Resolve inter-references: values like $ICLOUD in MC_PRIVATE expand
    # against os.environ + the rest of the env dict (order-independent).
    raw_env = {
        "MC_HOME": str(root),
        "MC_ID": machine_id,
        "MC_NAME": manifest.name or machine_id,
        **manifest.env,
    }
    script_env = {k: os.path.expandvars(v) for k, v in raw_env.items()}
    for _ in range(len(script_env)):  # converge chained references
        changed = False
        for key, value in script_env.items():
            new = value
            for k, v in script_env.items():
                new = new.replace(f"${k}", v)
            if new != value:
                script_env[key] = new
                changed = True
        if not changed:
            break

    # Two-phase script execution: init scripts prepare the environment
    # (package managers, OS features) before packages are installed.
    setup_scripts = [s for s in all_scripts if Path(s).name.startswith("init_")]
    post_scripts = [s for s in all_scripts if not Path(s).name.startswith("init_")]

    progress = Progress(
        TextColumn("{task.description:<10}", style="bold"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("[dim]{task.fields[current]}"),
        console=err_console,
    )
    t_files = t_bootstrap = t_packages = t_scripts = TaskID(0)

    with contextlib.ExitStack() as stack:
        if not settings.debug:
            stack.enter_context(mute_console_logging())
        stack.enter_context(progress)
        t_files = progress.add_task("Files", total=len(all_files), current="")
        t_bootstrap = progress.add_task("Init", total=len(setup_scripts), current="")
        t_packages = progress.add_task("Packages", total=len(all_packages), current="")
        t_scripts = progress.add_task("Scripts", total=len(post_scripts), current="")

        def _advance(task: TaskID, name: str) -> None:
            progress.update(task, advance=1, current=name)

        deploy_files(
            all_files,
            on_advance=lambda name: _advance(t_files, name),
        )
        run_scripts(
            setup_scripts,
            env=script_env,
            on_advance=lambda name: _advance(t_bootstrap, name),
        )
        install_packages(
            all_packages,
            on_advance=lambda name: _advance(t_packages, name),
        )
        run_scripts(
            post_scripts,
            env=script_env,
            on_advance=lambda name: _advance(t_scripts, name),
        )

    console.print("[bold green]Done![/]")


@app.command(rich_help_panel="Lifecycle")
def update(
    stash: bool = typer.Option(
        False, "-s", "--stash", help="Stash and reapply local changes."
    ),
    repo_only: bool = typer.Option(
        False, "-r", "--repo", help="Pull repo only; skip package upgrades."
    ),
) -> None:
    """Pull repo updates and upgrade installed packages."""
    from machine.app import upgrade_packages

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
        detail = (result.stderr or result.stdout or "").strip()
        console.print(f"[red]Pull failed.[/]")
        if detail:
            err_console.print(f"[dim]{detail}[/]")
        raise SystemExit(1)
    console.print("[green]Repo updated.[/]")

    if is_dirty and stash:
        subprocess.run([*git, "stash", "pop"])

    if repo_only:
        return

    console.print("Upgrading packages...")
    upgraded: list[str] = []
    upgrade_packages(on_advance=lambda mgr: upgraded.append(mgr))
    if upgraded:
        console.print(f"[green]Upgraded:[/] {', '.join(upgraded)}")
    else:
        console.print("[dim]No package managers found.[/]")


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

    from machine.app import _matches_platform

    all_scripts = [s for m in modules for s in m.scripts] + manifest.scripts
    all_scripts = [s for s in all_scripts if _matches_platform(Path(s))]
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
