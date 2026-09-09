"""Machine CLI application."""

import logging
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import click
import typer

from app.core import (
    PLATFORM,
    console,
    err_console,
    settings,
    setup_console_logging,
    setup_file_logging,
)
from app.ops.files import deploy_files, validate
from app.ops.packages import (
    cache_sudo,
    install_packages,
    select_package_source,
    validate_managers,
)
from app.ops.scripts import (
    build_script_env,
    filter_scripts,
    run_scripts,
    write_env_file,
)
from app.persistence import get_current_machine, save_current_machine

if TYPE_CHECKING:
    from app.machine import Machine, Module, Package, PkgManager

_logger = logging.getLogger(__name__)
CANONICAL_REPO_URL = "https://github.com/mohdfareed/machine.git"

# # MARK: App Entry Point

app = typer.Typer(
    help=settings.description,
    no_args_is_help=True,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

status_app = typer.Typer(help="Show machine information and local data.")
app.add_typer(status_app, name="status", rich_help_panel="Info")


def main(prog_name: str | None = None) -> None:
    """Entry point."""
    try:
        app(prog_name=prog_name)
    except SystemExit:
        raise  # successful or handled

    # Handle user interrupts.
    except KeyboardInterrupt:
        err_console.print("\n[dim]Interrupted.[/]")
        sys.exit(130)

    # Handle unexpected errors.
    except Exception as e:
        _logger.debug("Unhandled exception", exc_info=True)
        err_console.print(f"[bold red]Error:[/] {e}")
        err_console.print(f"[dim]See {settings.log_file}[/]")
        sys.exit(1)


# # MARK: Callbacks


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
    from app.machine import list_machines

    return list_machines(settings.home)


def get_modules() -> list[str]:
    from app.machine import list_modules

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


# # MARK: Lifecycle Commands


@app.command(rich_help_panel="Lifecycle")
def apply(
    machine: Annotated[
        str | None,
        typer.Option(
            "-m",
            "--machine",
            metavar="MACHINE",
            help=f"The machine to set up. <{'|'.join(machines.choices)}>",
            autocompletion=_complete_machines,
            click_type=machines,
            prompt=True,
        ),
    ] = get_current_machine() or None,
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
    from app.machine import load_manifest, resolve_modules

    root = settings.home
    if not machine:
        err_console.print("[red]No machine set. Run: mc apply[/]")
        raise SystemExit(1)

    manifest = load_manifest(machine, root)
    validate_managers(manifest.pkg_managers)
    save_current_machine(machine)
    write_env_file(machine, root)
    all_modules = resolve_modules(manifest.modules, root)
    module_filter = set(module_names)
    errors = validate(all_modules)

    if errors:
        for e in errors:
            err_console.print(f"[red]  {e}[/]")
        raise SystemExit(1)

    if module_filter:
        unknown = module_filter - {m.name for m in all_modules}
        if unknown:
            err_console.print(f"[red]Unknown modules: {', '.join(sorted(unknown))}[/]")
            raise SystemExit(1)

        active = [m for m in all_modules if m.name in module_filter or m.name == "core"]
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
    script_env["MC_PACKAGE_MANAGERS"] = " ".join(manifest.pkg_managers)
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
    failures: list[tuple[str, str, str]] = []

    _, file_failures = deploy_files(all_files, owners=owners)
    failures.extend(file_failures)
    init_failures = run_scripts(init_scripts, env=script_env, owners=owners)
    failures.extend(init_failures)

    if init_failures:
        _print_summary(failures, settings.log_file)
        return

    failures.extend(install_packages(all_packages, manifest.pkg_managers, owners=owners))
    failures.extend(run_scripts(post_scripts, env=script_env, owners=owners))

    _print_summary(failures, settings.log_file)


def _print_summary(failures: list[tuple[str, str, str]], log_file: Path) -> None:
    """Print a final status line. If there were failures, list each one."""
    if not failures:
        console.print(f"\n[bold green]Done![/] [dim](log: {log_file})[/]")
        return
    err_console.print(f"\n[bold yellow]Completed with {len(failures)} failure(s):[/]")

    for module, item, detail in failures:
        err_console.print(f"  [red]\\[{module}][/] {item} [dim]({detail})[/]")
    err_console.print(f"[dim]See {log_file}[/]")

    raise typer.Exit(1)


def _build_owners(
    active_modules: list["Module"],
    manifest: "Machine",
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
    from app.machine import load_manifest, resolve_modules

    root = settings.home
    machine_id = get_current_machine()
    if not machine_id:
        err_console.print("[red]No machine set. Run: mc apply[/]")
        raise SystemExit(1)

    manifest = load_manifest(machine_id, root)
    validate_managers(manifest.pkg_managers)
    all_modules = resolve_modules(manifest.modules, root)

    if module_names:
        unknown = set(module_names) - {m.name for m in all_modules}
        if unknown:
            err_console.print(f"[red]Unknown modules: {', '.join(sorted(unknown))}[/]")
            raise SystemExit(1)

        active = [m for m in all_modules if m.name in set(module_names) or m.name == "core"]
        raw_scripts = [s for m in active for s in m.scripts]
        all_packages = [p for m in active for p in m.packages]
    else:
        raw_scripts = [s for m in all_modules for s in m.scripts] + manifest.scripts
        all_packages = [p for m in all_modules for p in m.packages] + manifest.packages

    up_scripts = [s for s in filter_scripts(raw_scripts) if Path(s).name.startswith("up_")]
    script_packages = [p for p in all_packages if p.script and p.applies_to(PLATFORM)]
    if not up_scripts and not script_packages:
        console.print("[dim]No update actions found.[/]")
        return

    owners: dict[str, str] = {}
    for m in all_modules:
        for s in m.scripts:
            owners[s] = m.name
        for p in m.packages:
            owners[p.name] = m.name

    for s in manifest.scripts:
        owners.setdefault(s, machine_id)
    for p in manifest.packages:
        owners.setdefault(p.name, machine_id)

    script_env = build_script_env(machine_id, root)
    script_env["MC_PACKAGE_MANAGERS"] = " ".join(manifest.pkg_managers)
    mode = "[dim](dry-run)[/] " if settings.dry_run else ""
    console.print(f"{mode}Updating [bold]{machine_id}[/]")

    cache_sudo()
    failures = install_packages(
        script_packages,
        manifest.pkg_managers,
        owners=owners,
        rerun_script_packages=True,
    )

    failures.extend(run_scripts(up_scripts, env=script_env, owners=owners))
    _print_summary(failures, settings.log_file)


@app.command(rich_help_panel="Lifecycle")
def sync(
    no_apply: bool = typer.Option(False, "--no-apply", help="Skip apply after sync."),
) -> None:
    """Sync repo changes and re-run apply."""
    if settings.dry_run:
        console.print(f"[dim](dry-run)[/] Fetch main from {CANONICAL_REPO_URL}")
        return  # Skip in dry run mode.

    # Fetch and merge canonical main in the repo root.
    git = ["git", "-C", str(settings.home)]
    for args in (
        ["fetch", "--no-tags", CANONICAL_REPO_URL, "refs/heads/main"],
        ["merge", "--ff-only", "--autostash", "FETCH_HEAD"],
    ):
        # Failed on any marge/stash conflicts/errors.
        result = subprocess.run([*git, *args], capture_output=True, text=True)
        if result.returncode != 0:
            _logger.error("git %s failed:\n%s\n%s", " ".join(args), result.stdout, result.stderr)
            err_console.print("[red]Resolve the Git error, then run: mc sync[/]")
            raise SystemExit(1)

    # Verify merge. Autostash conflicts can leave merge's exit code at zero.
    result = subprocess.run([*git, "ls-files", "--unmerged"], capture_output=True, text=True)
    if result.returncode != 0:
        _logger.error("git ls-files failed:\n%s\n%s", result.stdout, result.stderr)
        err_console.print("[red]Could not check for conflicts.[/]")
        raise SystemExit(1)

    # Merge conflicts leave unmerged files in the index.
    if result.stdout.strip():
        err_console.print("[red]Could not restore local changes without conflicts.[/]")
        err_console.print("[dim]Resolve conflicts before applying.[/]")
        raise SystemExit(1)

    # Sync succeeded.
    console.print("[green]Synced with canonical main.[/]")
    if no_apply:
        return

    # Deploy the current machine.
    console.print()
    machine_id = get_current_machine()
    apply(machine=machine_id)


# # MARK: Info Commands


@app.command(rich_help_panel="Info")
def home() -> None:
    """Print the repo root path (MC_HOME)."""
    print(settings.home)


@app.command(rich_help_panel="Info")
def private() -> None:
    """Print the resolved MC_PRIVATE path for the current machine."""
    machine_id = get_current_machine()
    if not machine_id:
        err_console.print("[red]No machine set. Run: mc apply[/]")
        raise SystemExit(1)

    env = build_script_env(machine_id, settings.home)
    print(env["MC_PRIVATE"])


@status_app.callback(invoke_without_command=True)
def status(ctx: typer.Context) -> None:
    """Show machine home, app directory, and version."""
    if ctx.invoked_subcommand is not None:
        return

    console.print(f"[bold]{settings.name}[/] {settings.version}")
    machine = get_current_machine()

    console.print(f"  Machine: {machine or '[dim]none[/]'}")
    console.print(f"  Home:    {settings.home}")
    console.print(f"  Data:    {settings.app_dir}")


@status_app.command("id")
def status_id() -> None:
    """Print the current machine ID."""
    machine = get_current_machine()
    if not machine:
        err_console.print("No machine selected. Run mc apply -m <id> first.")
        raise typer.Exit(1)
    typer.echo(machine)


@status_app.command("state")
def status_state() -> None:
    """Print the saved script state."""
    path = settings.state_file
    if not path.exists():
        err_console.print("No saved script state found.")
        raise typer.Exit(1)
    typer.echo(path.read_text(encoding="utf-8"), nl=False)


@status_app.command("log")
def status_log() -> None:
    """Print the current log."""
    path = settings.log_file
    if not path.exists():
        err_console.print("No log file found.")
        raise typer.Exit(1)
    typer.echo(path.read_text(encoding="utf-8"), nl=False)


@app.command("list", rich_help_panel="Info")
def list_all() -> None:
    """List available machines and modules."""
    from app.machine import list_machines, list_modules

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
    from app.machine import load_manifest, resolve_modules

    root = settings.home
    manifest = load_manifest(machine, root)
    mods = resolve_modules(manifest.modules, root)
    root_prefix = str(root) + "/"

    def _short(path: str) -> str:
        return path.removeprefix(root_prefix)

    console.print(f"[bold]{machine}[/]")
    console.print(f"  Managers: {', '.join(manifest.pkg_managers) or 'none'}")
    if mods:
        console.print(f"  Modules: {', '.join(m.name for m in mods)}")

    # Files
    files = [(m.name, f) for m in mods for f in m.files if f.applies_to(PLATFORM)] + [
        (machine, f) for f in manifest.files if f.applies_to(PLATFORM)
    ]
    if files:
        console.print("\n[bold]Files:[/]")
        for mod, f in files:
            console.print(f"  [cyan]{mod:<12}[/] {_short(f.source)} → {f.target}")

    # Preserve module and declaration order, using the same script filtering as apply.
    all_scripts = [(m.name, script) for m in mods for script in filter_scripts(m.scripts)] + [
        (machine, script) for script in filter_scripts(manifest.scripts)
    ]
    pkgs = [(m.name, p) for m in mods for p in m.packages if p.applies_to(PLATFORM)] + [
        (machine, p) for p in manifest.packages if p.applies_to(PLATFORM)
    ]
    sections = [
        (
            "Init Scripts",
            [
                f"  [cyan]{mod:<12}[/] {_short(script)}"
                for mod, script in all_scripts
                if Path(script).name.startswith("init_")
            ],
        ),
        (
            "Packages",
            [
                f"  [cyan]{mod:<12}[/] {p.name} [dim]({_pkg_source(p, manifest.pkg_managers)})[/]"
                for mod, p in pkgs
            ],
        ),
        (
            "Scripts",
            [
                f"  [cyan]{mod:<12}[/] {_short(script)}"
                for mod, script in all_scripts
                if not Path(script).name.startswith(("init_", "up_"))
            ],
        ),
        (
            "Update Packages (mc update only)",
            [
                f"  [cyan]{mod:<12}[/] {p.name} [dim]({_pkg_source(p, manifest.pkg_managers)})[/]"
                for mod, p in pkgs
                if p.script
            ],
        ),
        (
            "Update Scripts (mc update only)",
            [
                f"  [cyan]{mod:<12}[/] {_short(script)}"
                for mod, script in all_scripts
                if Path(script).name.startswith("up_")
            ],
        ),
    ]

    for title, rows in sections:
        if rows:
            console.print(f"\n[bold]{title}:[/]")
            for row in rows:
                console.print(row)


def _pkg_source(p: "Package", managers: list["PkgManager"]) -> str:
    """Describe the package source selected for the current platform."""
    try:
        source = select_package_source(p, managers)
    except ValueError as exc:
        return str(exc)
    if source is not None:
        return f"{source}: {getattr(p, source)}"
    return "script" if p.script else "not applicable"
