"""Machine CLI application."""

import logging
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import click
import typer
from rich.prompt import Prompt

from machine.app import get_current_machine
from machine.core import console, err_console, settings, setup_console_logging, setup_file_logging

if TYPE_CHECKING:
    from machine.manifest import MachineManifest, Module, Package

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
        err_console.print(f"[dim]See {settings.app_dir / 'mc.log'}[/]")
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
        (n, "Machine (default)" if n == get_current_machine() else "Machine")
        for n in get_machines()
        if n.startswith(incomplete)
    ]


def _complete_modules(incomplete: str) -> list[tuple[str, str]]:
    return [(n, "Module") for n in get_modules() if n.startswith(incomplete)]


machines = click.Choice(get_machines(), case_sensitive=False)
modules = click.Choice(get_modules(), case_sensitive=False)


# MARK: Lifecycle Commands


@app.command(rich_help_panel="Lifecycle")
def apply(
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
    module_names: Annotated[
        list[str],
        typer.Argument(
            metavar="modules",
            help="Limit setup to the specified modules.",
            autocompletion=_complete_modules,
        ),
    ] = [],
) -> None:
    """Deploy configs, install packages, and run scripts."""
    from machine.app import (
        Failure,
        build_script_env,
        cache_sudo,
        deploy_files,
        filter_scripts,
        install_packages,
        run_scripts,
        save_current_machine,
        validate,
        write_env_file,
    )
    from machine.manifest import load_manifest, resolve_modules

    root = settings.home
    if not machine:
        err_console.print("[red]No machine set. Run: mc apply <machine>[/]")
        raise SystemExit(1)
    save_current_machine(machine)
    write_env_file(machine, root)

    manifest = load_manifest(machine, root)
    all_modules = resolve_modules(manifest.modules, root)
    module_filter = set(module_names)

    errors = validate(all_modules, machine)
    if errors:
        for e in errors:
            err_console.print(f"[red]  {e}[/]")
        raise SystemExit(1)

    if module_filter:
        unknown = module_filter - {m.name for m in all_modules}
        if unknown:
            err_console.print(f"[red]Unknown modules: {', '.join(sorted(unknown))}[/]")
            raise SystemExit(1)
        active = [m for m in all_modules if m.name in module_filter]
        all_files = [f for m in active for f in m.files]
        all_packages = [p for m in active for p in m.packages]
        raw_scripts = [s for m in active for s in m.scripts]
    else:
        active = all_modules
        all_files = [f for m in active for f in m.files] + manifest.files
        all_packages = [p for m in active for p in m.packages] + manifest.packages
        raw_scripts = [s for m in active for s in m.scripts] + manifest.scripts

    all_scripts = filter_scripts(raw_scripts)
    script_env = build_script_env(machine, root)
    owners = _build_owners(active, manifest, machine)

    mode = "[dim](dry-run)[/] " if settings.dry_run else ""
    console.print(f"{mode}Applying [bold]{machine}[/]")
    console.print(f"  Modules: {', '.join(m.name for m in active)}")

    init_scripts = [s for s in all_scripts if Path(s).name.startswith("init_")]
    post_scripts = [
        s
        for s in all_scripts
        if not Path(s).name.startswith("init_") and not Path(s).name.startswith("up_")
    ]

    cache_sudo()
    failures: list[Failure] = []

    _, file_failures = deploy_files(all_files, owners=owners)
    failures.extend(file_failures)
    failures.extend(run_scripts(init_scripts, env=script_env, owners=owners))
    failures.extend(install_packages(all_packages, owners=owners))
    failures.extend(run_scripts(post_scripts, env=script_env, owners=owners))

    _print_summary(failures, settings.app_dir / "mc.log")


def _print_summary(failures: list[tuple[str, str, str]], log_file: Path) -> None:
    """Print a final status line. If there were failures, list each one."""
    if not failures:
        console.print(f"\n[bold green]Done![/] [dim](log: {log_file})[/]")
        return
    err_console.print(f"\n[bold yellow]Completed with {len(failures)} failure(s):[/]")
    for module, item, detail in failures:
        err_console.print(f"  [red]\\[{module}][/] {item} [dim]({detail})[/]")
    err_console.print(f"[dim]See {log_file}[/]")


def _build_owners(
    active_modules: list["Module"],
    manifest: "MachineManifest",
    machine_id: str,
) -> dict[str, str]:
    """Build a single owner map for files, packages, and scripts."""
    owners: dict[str, str] = {}
    for m in active_modules:
        for s in m.scripts:
            owners[s] = m.name
        for f in m.files:
            owners[f.source] = m.name
        for p in m.packages:
            owners[p.name] = m.name
    for f in manifest.files:
        owners.setdefault(f.source, machine_id)
    for p in manifest.packages:
        owners.setdefault(p.name, machine_id)
    for s in manifest.scripts:
        owners.setdefault(s, machine_id)
    return owners


@app.command(rich_help_panel="Lifecycle")
def update(
    module_names: Annotated[
        list[str],
        typer.Argument(
            metavar="modules",
            help="Limit to the specified modules.",
            autocompletion=_complete_modules,
        ),
    ] = [],
) -> None:
    """Run up_* maintenance scripts for the current machine."""
    from machine.app import (
        Failure,
        build_script_env,
        cache_sudo,
        filter_scripts,
        get_current_machine,
        run_scripts,
    )
    from machine.manifest import load_manifest, resolve_modules

    root = settings.home
    machine_id = get_current_machine()
    if not machine_id:
        err_console.print("[red]No machine set. Run: mc apply <machine>[/]")
        raise SystemExit(1)

    manifest = load_manifest(machine_id, root)
    all_modules = resolve_modules(manifest.modules, root)

    if module_names:
        unknown = set(module_names) - {m.name for m in all_modules}
        if unknown:
            err_console.print(f"[red]Unknown modules: {', '.join(sorted(unknown))}[/]")
            raise SystemExit(1)
        active = [m for m in all_modules if m.name in set(module_names)]
        raw_scripts = [s for m in active for s in m.scripts]
    else:
        raw_scripts = [s for m in all_modules for s in m.scripts] + manifest.scripts

    up_scripts = [s for s in filter_scripts(raw_scripts) if Path(s).name.startswith("up_")]
    if not up_scripts:
        console.print("[dim]No update scripts found.[/]")
        return

    owners: dict[str, str] = {}
    for m in all_modules:
        for s in m.scripts:
            owners[s] = m.name
    for s in manifest.scripts:
        owners.setdefault(s, machine_id)

    script_env = build_script_env(machine_id, root)
    mode = "[dim](dry-run)[/] " if settings.dry_run else ""
    console.print(f"{mode}Updating [bold]{machine_id}[/]")

    cache_sudo()
    failures: list[Failure] = run_scripts(up_scripts, env=script_env, owners=owners)
    _print_summary(failures, settings.app_dir / "mc.log")


@app.command(rich_help_panel="Lifecycle")
def sync(
    stash: bool = typer.Option(False, "-s", "--stash", help="Stash changes before sync."),
    force: bool = typer.Option(False, "-f", "--force", help="Discard changes before sync."),
    push: bool = typer.Option(False, "-p", "--push", help="Push after pulling."),
    no_apply: bool = typer.Option(False, "--no-apply", help="Skip apply after sync."),
) -> None:
    """Pull repo changes and re-run apply."""
    if stash and force:
        err_console.print("[red]--stash and --force are mutually exclusive.[/]")
        raise SystemExit(1)

    if settings.dry_run:
        console.print("[dim](dry-run)[/] Would sync repo changes")
        return

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
            subprocess.run([*git, "stash", "push", "-m", "mc sync"])
            console.print("[yellow]Local changes stashed with message 'mc sync'.[/]")
            stashed = True

    result = subprocess.run([*git, "pull", "--rebase"], capture_output=True, text=True)
    if result.returncode != 0:
        subprocess.run([*git, "rebase", "--abort"], capture_output=True)
        _logger.error("git pull --rebase failed:\n%s\n%s", result.stdout, result.stderr)
        err_console.print("[red]Pull failed — rebase conflict or network error.[/]")
        err_console.print("[dim]Resolve conflicts manually, then run: mc sync[/]")
        raise SystemExit(1)
    console.print("[green]Pulled latest changes.[/]")

    if push:
        result = subprocess.run([*git, "push"], capture_output=True, text=True)
        if result.returncode != 0:
            _logger.error("git push failed:\n%s\n%s", result.stdout, result.stderr)
            err_console.print("[red]Push failed.[/]")
            err_console.print(f"[dim]{result.stderr.strip()}[/]")
            raise SystemExit(1)
        console.print("[green]Pushed local commits.[/]")

    if stashed:
        subprocess.run([*git, "stash", "pop"])

    if not no_apply:
        from machine.app import get_current_machine

        machine_id = get_current_machine()
        if machine_id:
            console.print()
            apply(machine=machine_id)
        else:
            console.print("[dim]No machine set — skipping apply.[/]")


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

    if choice == "abort":
        console.print("[dim]Aborted.[/]")
        raise SystemExit(0)
    if choice == "discard":
        if not typer.confirm("This cannot be undone. Are you sure?"):
            console.print("[dim]Aborted.[/]")
            raise SystemExit(0)
        return True
    return False


# MARK: Info Commands


@app.command(rich_help_panel="Info")
def home() -> None:
    """Print the repo root path (MC_HOME)."""
    print(settings.home)


@app.command(rich_help_panel="Info")
def private() -> None:
    """Print the resolved MC_PRIVATE path for the current machine."""
    from machine.app import build_script_env, get_current_machine

    machine_id = get_current_machine()
    if not machine_id:
        err_console.print("[red]No machine set. Run: mc apply <machine>[/]")
        raise SystemExit(1)

    env = build_script_env(machine_id, settings.home)
    path = env.get("MC_PRIVATE", "")
    if not path:
        err_console.print("[red]MC_PRIVATE is not set for this machine.[/]")
        raise SystemExit(1)
    print(path)


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


@app.command("list", rich_help_panel="Info")
def list_all() -> None:
    """List available machines and modules."""
    from machine.manifest import list_machines, list_modules

    root = settings.home
    for label, names in [("Machines", list_machines(root)), ("Modules", list_modules(root))]:
        if names:
            console.print(f"[bold]{label}:[/]")
            for name in names:
                console.print(f"  {name}")
        else:
            console.print(f"[dim]No {label.lower()} found[/]")


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
    from machine.app import matches_platform
    from machine.manifest import load_manifest, resolve_modules

    root = settings.home
    manifest = load_manifest(machine, root)
    mods = resolve_modules(manifest.modules, root)
    root_prefix = str(root) + "/"

    def _short(path: str) -> str:
        return path.removeprefix(root_prefix)

    console.print(f"[bold]{machine}[/]")
    if mods:
        console.print(f"  Modules: {', '.join(m.name for m in mods)}")

    # Files
    files = [(m.name, f) for m in mods for f in m.files] + [(machine, f) for f in manifest.files]
    if files:
        console.print("\n[bold]Files:[/]")
        for mod, f in files:
            console.print(f"  [cyan]{mod:<12}[/] {_short(f.source)} → {f.target}")

    # Packages
    pkgs = [(m.name, p) for m in mods for p in m.packages] + [
        (machine, p) for p in manifest.packages
    ]
    if pkgs:
        console.print("\n[bold]Packages:[/]")
        for mod, p in pkgs:
            console.print(f"  [cyan]{mod:<12}[/] {p.name} [dim]({_pkg_sources(p)})[/]")

    # Scripts (grouped by phase)
    all_scripts = [(m.name, s) for m in mods for s in m.scripts] + [
        (machine, s) for s in manifest.scripts
    ]
    for title, prefix_test in [
        ("Init Scripts", lambda n: n.startswith("init_")),
        ("Scripts", lambda n: not n.startswith(("init_", "up_", "_"))),
        ("Update Scripts", lambda n: n.startswith("up_")),
    ]:
        group = [
            (mod, s)
            for mod, s in all_scripts
            if matches_platform(Path(s))
            and not Path(s).stem.startswith("_")
            and prefix_test(Path(s).name)
        ]
        if group:
            console.print(f"\n[bold]{title}:[/]")
            for mod, s in group:
                console.print(f"  [cyan]{mod:<12}[/] {_short(s)}")


def _pkg_sources(p: "Package") -> str:
    """Format package install sources as a short string."""
    sources: list[str] = []
    for attr in ("brew", "apt", "snap", "winget", "scoop"):
        val = getattr(p, attr, None)
        if val:
            sources.append(f"{attr}: {val}")
    if p.mas is not None:
        sources.append(f"mas: {p.mas}")
    if p.script:
        sources.append("script")
    return ", ".join(sources)
