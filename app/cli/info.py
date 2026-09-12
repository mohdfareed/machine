"""Inspect machine configuration and local data."""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from app import reporting
from app.cli.entry import complete_machines, get_current_machine, validate_machine
from app.env import PLATFORM, build_env, settings
from app.ops.packages import select_package_source
from app.ops.scripts import filter_scripts

if TYPE_CHECKING:
    from app.models import Package, PkgManager

status_app = typer.Typer(help="Show machine information and local data.")

# =============================================================================
# MARK: Info Commands
# =============================================================================


def home() -> None:
    """Print the repo root path (MC_HOME)."""
    print(settings.home)


def private() -> None:
    """Print the resolved MC_PRIVATE path for the current machine."""
    machine_id = get_current_machine()
    if not machine_id:
        reporting.error("No machine selected.")
        raise SystemExit(1)

    env = build_env(machine_id, settings.home)
    print(env["MC_PRIVATE"])


@status_app.callback(invoke_without_command=True)
def status(ctx: typer.Context) -> None:
    """Show machine home, app directory, and version."""
    if ctx.invoked_subcommand is not None:
        return

    reporting.heading(f"{settings.name} {settings.version}")
    machine = get_current_machine()

    reporting.detail(f"Machine: {machine or 'none'}")
    reporting.detail(f"Home: {settings.home}")
    reporting.detail(f"Data: {settings.app_dir}")


@status_app.command("id")
def status_id() -> None:
    """Print the current machine ID."""
    machine = get_current_machine()
    if not machine:
        reporting.error("No machine selected.")
        raise typer.Exit(1)

    typer.echo(machine)


@status_app.command("state")
def status_state() -> None:
    """Print the script-state file path."""
    typer.echo(settings.state_file)


@status_app.command("log")
def status_log() -> None:
    """Print the log file path."""
    typer.echo(settings.log_file)


def list_all() -> None:
    """List available machines and modules."""
    from app.discovery import list_machines, list_modules

    root = settings.home
    for label, names in [("Machines", list_machines(root)), ("Modules", list_modules(root))]:
        if not names:
            reporting.detail(f"No {label.lower()} found.")
            continue

        reporting.heading(label)
        for name in names:
            reporting.detail(name)


# =============================================================================
# MARK: Show Machine Command
# =============================================================================


def show(
    machine: Annotated[
        str,
        typer.Option(
            "-m",
            "--machine",
            metavar="MACHINE",
            help="The machine to inspect.",
            autocompletion=complete_machines,
            callback=validate_machine,
            prompt=True,
        ),
    ] = get_current_machine() or "",
) -> None:
    """Show resolved configuration for a machine."""

    from app.machine import load_machine

    # Resolve the machine configuration.
    root = settings.home
    manifest, mods = load_machine(machine, root)
    root_prefix = str(root) + os.sep

    def _short(path: str) -> str:
        return path.removeprefix(root_prefix)

    # Show the machine and its selected managers and modules.
    reporting.heading(machine)
    reporting.detail(f"Managers: {', '.join(manifest.pkg_managers) or 'none'}")
    if mods:
        reporting.detail(f"Modules: {', '.join(m.name for m in mods)}")

    # Show files for the current platform.
    files = [(m.name, f) for m in mods for f in m.files if f.applies_to(PLATFORM)] + [
        (machine, f) for f in manifest.files if f.applies_to(PLATFORM)
    ]
    if files:
        reporting.heading("Files")
        for mod, f in files:
            reporting.detail(f"{mod} · {_short(f.source)} → {f.target}")

    # Build execution sections in module and declaration order.
    # Use the same script filtering as deploy.
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
                f"{mod} · {_short(script)}"
                for mod, script in all_scripts
                if Path(script).name.startswith("init_")
            ],
        ),
        (
            "Packages",
            [f"{mod} · {p.name} ({_pkg_source(p, manifest.pkg_managers)})" for mod, p in pkgs],
        ),
        (
            "Scripts",
            [
                f"{mod} · {_short(script)}"
                for mod, script in all_scripts
                if not Path(script).name.startswith(("init_", "up_"))
            ],
        ),
        (
            "Maintenance Packages",
            [
                f"{mod} · {p.name} ({_pkg_source(p, manifest.pkg_managers)})"
                for mod, p in pkgs
                if p.script
            ],
        ),
        (
            "Maintenance Scripts",
            [
                f"{mod} · {_short(script)}"
                for mod, script in all_scripts
                if Path(script).name.startswith("up_")
            ],
        ),
    ]

    # Show populated execution sections.
    for title, rows in sections:
        if not rows:
            continue

        reporting.heading(title)
        for row in rows:
            reporting.detail(row)


def _pkg_source(p: "Package", managers: list["PkgManager"]) -> str:
    try:
        source = select_package_source(p, managers)
    except ValueError as exc:
        return str(exc)

    if source is None:
        return "script" if p.script else "unknown"
    return f"{source}: {p.sources[source]}"
