"""Machine CLI application."""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import click
import typer
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from machine.app import get_current_machine
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
    except SystemExit:
        raise
    except KeyboardInterrupt:
        err_console.print("\n[dim]Interrupted.[/]")
        sys.exit(130)
    except Exception as e:
        _logger.debug("Unhandled exception", exc_info=True)
        err_console.print(f"[bold red]Error:[/] {e}")
        log_file = settings.app_dir / "mc.log"
        err_console.print(f"[dim]See {log_file}[/]")
        sys.exit(1)


# MARK: Callbacks


@app.callback()
def callback(
    debug: bool = typer.Option(False, "-d", "--debug", help="Enable debug logging."),
    dry_run: bool = typer.Option(
        False, "-n", "--dry-run", help="Preview changes without applying."
    ),
    version: bool = typer.Option(False, "-v", "--version", help="Show version and exit."),
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


def get_machines() -> list[str]:
    from machine.manifest import list_machines

    return list_machines(settings.home)


def get_modules() -> list[str]:
    from machine.manifest import list_modules

    return list_modules(settings.home)


def _complete_machines(incomplete: str) -> list[tuple[str, str]]:
    return [
        (
            n,
            "Machine (default)" if n == get_current_machine() else "Machine",
        )
        for n in get_machines()
        if n.startswith(incomplete)
    ]


def _complete_modules(incomplete: str) -> list[tuple[str, str]]:
    return [(n, "Module") for n in get_modules() if n.startswith(incomplete)]


machines = click.Choice(get_machines(), case_sensitive=False)
modules = click.Choice(get_modules(), case_sensitive=False)


def _print_summary(failures: list[tuple[str, str, str]], log_file: Path) -> None:
    """Print a final status line. If there were failures, list each one."""
    if not failures:
        console.print(f"\n[bold green]Done![/] [dim](log: {log_file})[/]")
        return

    err_console.print(f"\n[bold yellow]Completed with {len(failures)} failure(s):[/]")
    for module, item, detail in failures:
        err_console.print(f"  [red]\\[{module}][/] {item} [dim]({detail})[/]")
    err_console.print(f"[dim]See {log_file}[/]")


# MARK: Lifecycle Commands


@app.command(rich_help_panel="Lifecycle")
def setup(
    machine: Annotated[
        str,
        typer.Option(
            "-m",
            "--machine",
            metavar="MACHINE",
            help="The machine to set up.",
            autocompletion=_complete_machines,
            click_type=machines,
            prompt=True,
        ),
    ] = get_current_machine() or "",
    modules: Annotated[
        list[str],
        typer.Argument(
            help="Limit setup to the specified modules.",
            autocompletion=_complete_modules,
        ),
    ] = [],
) -> None:
    """Deploy configs, install packages, and run scripts.

    Pass a machine ID to set it as the current machine, or omit it to
    reuse the last-used machine.  Optionally list module names after to
    run only those modules.
    """
    from machine.app import (
        Failure,
        build_script_env,
        deploy_files,
        filter_scripts,
        install_packages,
        run_scripts,
        save_current_machine,
        validate,
    )
    from machine.manifest import load_manifest, load_module

    root = settings.home
    machine_id = machine
    if not machine_id:
        err_console.print("[red]No machine set. Run: mc setup <machine>[/]")
        raise SystemExit(1)
    save_current_machine(machine_id)
    module_filter = set(modules)

    manifest = load_manifest(machine_id, root)
    all_modules = [load_module(m, root) if isinstance(m, str) else m for m in manifest.modules]

    errors = validate(all_modules, manifest.env, machine_id)
    if errors:
        for e in errors:
            _logger.error("Validation: %s", e)
            err_console.print(f"[red]  {e}[/]")
        raise SystemExit(1)

    if module_filter:
        unknown = module_filter - {m.name for m in all_modules}
        if unknown:
            err_console.print(f"[red]Unknown modules: {', '.join(sorted(unknown))}[/]")
            raise SystemExit(1)
        active_modules = [m for m in all_modules if m.name in module_filter]
        all_files = [f for m in active_modules for f in m.files]
        all_packages = [p for m in active_modules for p in m.packages]
        raw_scripts = [s for m in active_modules for s in m.scripts]
    else:
        active_modules = all_modules
        all_files = [f for m in active_modules for f in m.files] + manifest.files
        all_packages = [p for m in active_modules for p in m.packages] + manifest.packages
        raw_scripts = [s for m in active_modules for s in m.scripts] + manifest.scripts

    all_scripts = filter_scripts(raw_scripts)
    script_env = build_script_env(manifest, machine_id, root)

    # Build ownership maps for module context in log messages
    script_owners: dict[str, str] = {}
    file_owners: dict[str, str] = {}
    pkg_owners: dict[str, str] = {}
    for m in active_modules:
        for s in m.scripts:
            script_owners[s] = m.name
        for f in m.files:
            file_owners[f.source] = m.name
        for p in m.packages:
            pkg_owners[p.name] = m.name
    # Tag manifest-level items with the machine ID
    for f in manifest.files:
        file_owners.setdefault(f.source, machine_id)
    for p in manifest.packages:
        pkg_owners.setdefault(p.name, machine_id)
    for s in manifest.scripts:
        script_owners.setdefault(s, machine_id)

    mode = "[dim](dry-run)[/] " if settings.dry_run else ""
    console.print(f"{mode}Setting up [bold]{machine_id}[/]")
    console.print(f"  Modules: {', '.join(m.name for m in active_modules)}")

    # init_* prepares env/tools before packages; upgrade_* is for mc upgrade only
    setup_scripts = [s for s in all_scripts if Path(s).name.startswith("init_")]
    post_scripts = [
        s
        for s in all_scripts
        if not Path(s).name.startswith("init_") and not Path(s).name.startswith("upgrade_")
    ]

    log_file = settings.app_dir / "mc.log"
    failures: list[Failure] = []
    if settings.debug:
        # Debug mode — no progress bar, full logging to console
        _, file_failures = deploy_files(all_files, owners=file_owners)
        failures.extend(file_failures)
        failures.extend(run_scripts(setup_scripts, env=script_env, owners=script_owners))
        failures.extend(install_packages(all_packages, owners=pkg_owners))
        failures.extend(run_scripts(post_scripts, env=script_env, owners=script_owners))
    else:
        total = len(all_files) + len(setup_scripts) + len(all_packages) + len(post_scripts)
        progress = Progress(
            TextColumn("[bold]{task.fields[phase]:<10}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[dim]{task.fields[current]}"),
            console=err_console,
            transient=True,
        )

        with progress:
            task = progress.add_task("setup", total=total, phase="Files", current="")
            paused = False

            def _advance(name: str) -> None:
                progress.advance(task)
                progress.update(task, current=name)

            def _pause(_name: str = "") -> None:
                nonlocal paused
                progress.stop()
                paused = True

            def _resume(name: str) -> None:
                nonlocal paused
                if paused:
                    progress.start()
                    paused = False
                progress.advance(task)
                progress.update(task, current=name)

            _, file_failures = deploy_files(all_files, on_advance=_advance, owners=file_owners)
            failures.extend(file_failures)
            progress.update(task, phase="Init")

            failures.extend(
                run_scripts(
                    setup_scripts,
                    env=script_env,
                    on_before=_pause,
                    on_after=_resume,
                    owners=script_owners,
                )
            )
            progress.update(task, phase="Packages")

            failures.extend(
                install_packages(
                    all_packages,
                    on_before=_pause,
                    on_after=_resume,
                    owners=pkg_owners,
                )
            )
            progress.update(task, phase="Scripts")

            failures.extend(
                run_scripts(
                    post_scripts,
                    env=script_env,
                    on_before=_pause,
                    on_after=_resume,
                    owners=script_owners,
                )
            )

    _print_summary(failures, log_file)


@app.command(rich_help_panel="Lifecycle")
def upgrade(
    modules: Annotated[
        list[str],
        typer.Argument(
            help="Limit setup to the specified modules.",
            autocompletion=_complete_modules,
        ),
    ] = [],
) -> None:
    """Run upgrade_* scripts for the current machine."""
    from machine.app import (
        Failure,
        build_script_env,
        filter_scripts,
        get_current_machine,
        run_scripts,
    )
    from machine.manifest import load_manifest, load_module

    root = settings.home
    machine_id = get_current_machine()
    if not machine_id:
        err_console.print("[red]No machine set. Run: mc setup <machine>[/]")
        raise SystemExit(1)

    manifest = load_manifest(machine_id, root)
    all_modules = [load_module(m, root) if isinstance(m, str) else m for m in manifest.modules]

    if modules:
        unknown = set(modules) - {m.name for m in all_modules}
        if unknown:
            err_console.print(f"[red]Unknown modules: {', '.join(sorted(unknown))}[/]")
            raise SystemExit(1)
        active = [m for m in all_modules if m.name in set(modules)]
        raw_scripts = [s for m in active for s in m.scripts]
    else:
        raw_scripts = [s for m in all_modules for s in m.scripts] + manifest.scripts

    upgrade_scripts = [
        s for s in filter_scripts(raw_scripts) if Path(s).name.startswith("upgrade_")
    ]

    if not upgrade_scripts:
        console.print("[dim]No upgrade scripts found.[/]")
        return

    script_owners: dict[str, str] = {}
    for m in all_modules:
        for s in m.scripts:
            script_owners[s] = m.name
    for s in manifest.scripts:
        script_owners.setdefault(s, machine_id)

    script_env = build_script_env(manifest, machine_id, root)
    mode = "[dim](dry-run)[/] " if settings.dry_run else ""
    console.print(f"{mode}Upgrading [bold]{machine_id}[/]")
    log_file = settings.app_dir / "mc.log"

    failures: list[Failure] = []
    if settings.debug:
        failures = run_scripts(upgrade_scripts, env=script_env, owners=script_owners)
    else:
        progress = Progress(
            TextColumn("[bold]{task.fields[phase]:<10}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[dim]{task.fields[current]}"),
            console=err_console,
            transient=True,
        )
        with progress:
            task = progress.add_task(
                "upgrade", total=len(upgrade_scripts), phase="Upgrade", current=""
            )
            paused = False

            def _pause(_name: str = "") -> None:
                nonlocal paused
                progress.stop()
                paused = True

            def _resume(name: str) -> None:
                nonlocal paused
                if paused:
                    progress.start()
                    paused = False
                progress.advance(task)
                progress.update(task, current=name)

            failures.extend(
                run_scripts(
                    upgrade_scripts,
                    env=script_env,
                    on_before=_pause,
                    on_after=_resume,
                    owners=script_owners,
                )
            )

    _print_summary(failures, log_file)


@app.command(rich_help_panel="Lifecycle")
def update(
    stash: bool = typer.Option(
        False, "-s", "--stash", help="Stash local changes and reapply after pull."
    ),
    force: bool = typer.Option(False, "-f", "--force", help="Discard local changes before pull."),
) -> None:
    """Pull the latest repo changes."""
    if stash and force:
        err_console.print("[red]--stash and --force are mutually exclusive.[/]")
        raise SystemExit(1)

    root = settings.home
    git = ["git", "-C", str(root)]

    result = subprocess.run([*git, "status", "--porcelain"], capture_output=True, text=True)
    is_dirty = bool(result.stdout.strip())

    stashed = False
    if is_dirty:
        if _prompt_force(stash=stash, force=force):
            subprocess.run([*git, "fetch", "--all"], capture_output=True)
            subprocess.run([*git, "reset", "--hard", "origin/HEAD"])
            console.print("[yellow]Local changes discarded.[/]")
        else:
            subprocess.run([*git, "stash", "push", "-m", "mc update"])
            console.print("[yellow]Local changes stashed.[/]")
            stashed = True

    result = subprocess.run([*git, "pull", "--ff-only"], capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        err_console.print("[red]Pull failed.[/]")
        if detail:
            err_console.print(f"[dim]{detail}[/]")
        raise SystemExit(1)
    console.print("[green]Repo updated.[/]")

    if stashed:
        subprocess.run([*git, "stash", "pop"])


def _prompt_force(stash: bool, force: bool) -> bool:
    if force:
        choice = "discard"
    elif stash:
        choice = "stash"
    else:
        choice = Prompt.ask(
            "[yellow]Local changes detected.[/]",
            choices=["stash", "discard", "abort"],
            default="abort",
        )

    aborted = False
    if choice == "stash":
        force = False
        aborted = False
    elif choice == "discard":
        force = True
        aborted = not typer.confirm("[red]This cannot be undone.[/]")
    else:  # abort
        force = False
        aborted = True

    if aborted:
        console.print("[dim]Aborted.[/]")
        raise SystemExit(0)
    return force


# MARK: Info Commands


@app.command(rich_help_panel="Info")
def info() -> None:
    """Show machine home, app directory, and version."""
    from machine.app import get_current_machine

    console.print(f"[bold]{settings.name}[/] {settings.version}")
    machine = get_current_machine()
    if machine:
        console.print(f"  Machine: {machine}")
    console.print(f"  Home:    {settings.home}")
    console.print(f"  Data:    {settings.app_dir}")
    console.print(f"  Logs:    {settings.app_dir / 'mc.log'}")
    console.print(f"  State:   {settings.app_dir / 'state.json'}")


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
    machine: Annotated[
        str,
        typer.Option(
            "-m",
            "--machine",
            metavar="MACHINE",
            help="The machine to inspect.",
            autocompletion=_complete_machines,
            click_type=machines,
            prompt=True,
        ),
    ] = get_current_machine() or "",
) -> None:
    """Show resolved configuration for a machine."""
    from machine.manifest import load_manifest, load_module

    root = settings.home
    manifest = load_manifest(machine, root)
    modules = [load_module(m, root) if isinstance(m, str) else m for m in manifest.modules]

    console.print(f"[bold]{machine}[/]")
    if modules:
        console.print(f"\n[bold]Modules:[/] {', '.join(m.name for m in modules)}")

    # Show only manifest env (MC_HOME/MC_ID are runtime, not config)
    if manifest.env:
        console.print("\n[bold]Environment:[/]")
        for k, v in manifest.env.items():
            console.print(f"  {k}={v}")

    # Helper: shorten absolute paths relative to repo root
    root_prefix = str(root) + "/"

    def _short(path: str) -> str:
        return path.removeprefix(root_prefix)

    # Build (item, module_name) pairs for files, packages, scripts
    tagged_files: list[tuple[str, str, str]] = []
    for m in modules:
        for f in m.files:
            tagged_files.append((_short(f.source), f.target, m.name))
    for f in manifest.files:
        tagged_files.append((_short(f.source), f.target, machine))

    if tagged_files:
        table = Table(title="Files", show_header=True)
        table.add_column("Module", style="cyan")
        table.add_column("Source", style="dim")
        table.add_column("Target")
        for src, tgt, mod in tagged_files:
            table.add_row(mod, src, tgt)
        console.print()
        console.print(table)

    tagged_pkgs: list[tuple[str, str, str]] = []
    for m in modules:
        for p in m.packages:
            tagged_pkgs.append((p.name, _pkg_sources(p), m.name))
    for p in manifest.packages:
        tagged_pkgs.append((p.name, _pkg_sources(p), machine))

    if tagged_pkgs:
        table = Table(title="Packages", show_header=True)
        table.add_column("Module", style="cyan")
        table.add_column("Name")
        table.add_column("Source", style="dim")
        for name, sources, mod in tagged_pkgs:
            table.add_row(mod, name, sources)
        console.print()
        console.print(table)

    from machine.app import matches_platform

    # Split scripts into three groups, tagged with module
    init_scripts: list[tuple[str, str]] = []
    upgrade_scripts: list[tuple[str, str]] = []
    post_scripts: list[tuple[str, str]] = []

    def _bucket(name: str) -> list[tuple[str, str]]:
        if name.startswith("init_"):
            return init_scripts
        if name.startswith("upgrade_"):
            return upgrade_scripts
        return post_scripts

    for m in modules:
        for s in m.scripts:
            if matches_platform(Path(s)):
                _bucket(Path(s).name).append((_short(s), m.name))
    for s in manifest.scripts:
        if matches_platform(Path(s)):
            _bucket(Path(s).name).append((_short(s), machine))

    for title, group in [
        ("Init Scripts", init_scripts),
        ("Scripts", post_scripts),
        ("Upgrade Scripts", upgrade_scripts),
    ]:
        if group:
            table = Table(title=title, show_header=True)
            table.add_column("Module", style="cyan")
            table.add_column("Script", style="dim")
            for s, mod in group:
                table.add_row(mod, s)
            console.print()
            console.print(table)


def _pkg_sources(p: "Package") -> str:  # type: ignore[name-defined]
    """Format package install sources as a short string."""
    sources: list[str] = []
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
    return ", ".join(sources)
