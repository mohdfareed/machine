"""Inspect selected configuration without preparing execution."""

from typing import Annotated

import typer

from app import cli, env, reporting
from app.discovery import list_machines, list_modules
from app.env import get_current_machine
from app.machine import load_machine
from app.validation import validate_managers

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Info Commands
# ═════════════════════════════════════════════════════════════════════════════


def validate(
    machine: Annotated[
        str | None,
        typer.Option("-m", "--machine", autocompletion=cli.complete_machines),
    ] = None,
) -> None:
    """Check configuration, inputs, and manager availability without deploying."""
    machine = cli.validate_machine(machine or get_current_machine())
    if machine is None:
        raise ValueError("No machine selected. Pass --machine to validate a configuration.")
    configuration = load_machine(machine, validate=True)
    validate_managers(configuration.pkg_managers, env=configuration.env)
    reporting.success(f"Configuration valid: {machine} ({env.PLATFORM})")


def machine_id() -> None:
    """Print the saved machine ID."""
    reporting.plain(get_current_machine() or "")


def home() -> None:
    """Print the repository root."""
    reporting.plain(str(env.ROOT))


def list_mc() -> None:
    """List available machines."""
    if not (machines := list_machines()):
        reporting.detail("No machines found.")
        return

    reporting.heading("Machines")
    for mc in machines:
        reporting.detail(mc)


def list_mod() -> None:
    """List available modules."""
    if not (modules := list_modules()):
        reporting.detail("No modules found.")
        return

    reporting.heading("Modules")
    for mod in modules:
        reporting.detail(mod)


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Show Machine Command
# ═════════════════════════════════════════════════════════════════════════════


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
    """Inspect machine configuration and deployment."""
    if context.invoked_subcommand is not None:
        return

    # Resolve the selection and applicable declarations.
    machine = machine or get_current_machine() or reporting.prompt("Machine", list_machines())
    machine = cli.validate_machine(machine)
    if machine is None:
        raise ValueError("No machine selected.")
    configuration = load_machine(machine)

    # Report. ─────────────────────────────────────────────────────────────────

    reporting.heading(f"Machine [{machine}]")

    reporting.heading("Scripts")
    for script in configuration.scripts:
        reporting.path(script, root=env.ROOT)

    reporting.heading("Packages")
    reporting.grid([package.name for package in configuration.packages])

    reporting.heading("Files")
    for file in configuration.files:
        reporting.link(file.source, file.target, root=env.ROOT)
        reporting.plain("")
    reporting.detail(f"Total files: {len(configuration.files)}")
