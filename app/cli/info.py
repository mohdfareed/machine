"""Inspect selected configuration without preparing execution."""

from pathlib import Path
from typing import Annotated

import typer

from app import cli, env, reporting
from app.discovery import list_machines, list_modules
from app.env import build_env, get_current_machine
from app.machine import load_machine

# =============================================================================
# MARK: Info Commands
# =============================================================================


def machine_id() -> None:
    """Print the saved machine ID."""
    reporting.plain(get_current_machine() or "")


def home() -> None:
    """Print the repository root."""
    reporting.plain(str(env.ROOT))


def private() -> None:
    """Print the private storage path."""
    machine_id = get_current_machine()
    if not machine_id:
        raise ValueError(f"No machine selected. Select one with {cli.COMMAND} deploy.")
    reporting.plain(build_env(machine_id, include_private=False)["MC_PRIVATE"])


def status() -> None:
    """Show the selected machine, repo and CLI version."""
    reporting.heading(f"{cli.NAME} {cli.VERSION}")
    reporting.detail(f"Machine: {get_current_machine() or 'none'}")
    reporting.detail(f"Home: {env.ROOT}")


def list_all() -> None:
    """List available machines and modules."""
    for label, names in [("Machines", list_machines()), ("Modules", list_modules())]:
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
    context: typer.Context,
    machine: Annotated[
        str | None,
        typer.Option(
            "-m",
            "--machine",
            metavar="MACHINE",
            help="The machine to inspect.",
            autocompletion=cli.complete_machines,
        ),
    ] = None,
) -> None:
    """Inspect machine information; without a subcommand, show resolved configuration."""
    if context.invoked_subcommand is not None:
        return

    # Resolve the selection and applicable declarations without loading secrets.
    machine = machine or get_current_machine() or reporting.prompt("Machine", list_machines())
    machine = cli.validate_machine(machine)
    if machine is None:
        raise ValueError("No machine selected.")
    machine_env = build_env(machine, include_private=False)
    configuration = load_machine(machine, env=machine_env)

    # Describe selected inputs without reconstructing the execution workflow.
    reporting.heading(f"Machine: {machine}")
    reporting.detail(f"Managers: {', '.join(configuration.pkg_managers) or 'none'}")
    reporting.detail(f"Modules: {', '.join(configuration.modules)}")

    reporting.heading("Files")
    for file in configuration.files:
        source = Path(file.source)
        display = source.relative_to(env.ROOT) if source.is_relative_to(env.ROOT) else source
        reporting.detail(f"{display} → {file.target}")

    reporting.heading("Packages")
    for package in configuration.packages:
        reporting.detail(package.name)

    reporting.heading("Scripts")
    for value in configuration.scripts:
        script = Path(value)
        display = script.relative_to(env.ROOT) if script.is_relative_to(env.ROOT) else script
        reporting.detail(str(display))
