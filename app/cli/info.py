"""Inspect selected configuration without preparing execution."""

from typing import Annotated

import typer

from app import cli, env, reporting
from app.discovery import list_machines, list_modules
from app.env import build_env, get_current_machine
from app.machine import load_machine

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Info Commands
# ═════════════════════════════════════════════════════════════════════════════


def machine_id() -> None:
    """Print the saved machine ID."""
    reporting.plain(get_current_machine() or "")


def home() -> None:
    """Print the repository root."""
    reporting.plain(str(env.ROOT))


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
    """Inspect machine information; without a subcommand, show resolved configuration."""
    if context.invoked_subcommand is not None:
        return

    # Resolve the selection and applicable declarations without loading secrets.
    machine = machine or get_current_machine() or reporting.prompt("Machine", list_machines())
    machine = cli.validate_machine(machine)
    if machine is None:
        raise ValueError("No machine selected.")
    machine_env = build_env(machine)
    configuration = load_machine(machine, env=machine_env)

    # Print report. ───────────────────────────────────────────────────────────

    reporting.heading(f"Machine [{machine}]")
    reporting.detail(f"Managers: {' | '.join(configuration.pkg_managers) or 'none'}")

    reporting.heading("Modules")
    reporting.grid(configuration.modules)

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
