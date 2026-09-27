"""Upgrade packages and run maintenance for the selected machine."""

from typing import Annotated

import typer

from app import cli
from app.config.loader import load_machine
from app.deployment.managers import upgrade_managers
from app.deployment.packages import upgrade_packages
from app.deployment.scripts import run_scripts
from app.runtime import reporting
from app.runtime.env import get_current_machine

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Upgrade Command
# ═════════════════════════════════════════════════════════════════════════════


def upgrade(
    module_names: Annotated[
        list[str],
        typer.Argument(
            metavar="MODULES",
            help="Limit custom maintenance to these modules and their prerequisites.",
            autocompletion=cli.complete_modules,
        ),
    ] = [],
    dry_run: Annotated[
        bool, typer.Option("-n", "--dry-run", help="Preview changes without applying them.")
    ] = False,
) -> None:
    """Upgrade configured managers and run custom maintenance."""
    if dry_run:
        reporting.heading("Dry run: no changes will be made.")

    # Resolve the selected configuration.
    machine_id = get_current_machine()
    if not machine_id:
        raise ValueError(f"No machine selected. Select one with {cli.COMMAND} deploy.")
    configuration = load_machine(machine_id, module_names)
    env = configuration.env

    # Summarize this invocation.
    reporting.heading(f"Machine [{machine_id}]")
    reporting.detail(f"Managers: {' | '.join(configuration.pkg_managers) or 'none'}")

    # Debug info.
    reporting.debug(f"Command: {upgrade.__name__} ({'dry run' if dry_run else 'execute'})")
    reporting.debug(f"Modules: {', '.join(module_names) or 'all declared modules'}")
    reporting.debug(
        f"Inputs: "
        f"{len(configuration.modules)} modules, "
        f"{len(configuration.files)} files, "
        f"{len(configuration.scripts)} scripts, "
        f"{len(configuration.packages)} packages."
    )

    # Upgrade all packages owned by the platform's fixed managers.
    reporting.heading("Upgrading managers and all their packages")
    upgrade_managers(configuration.pkg_managers, env=env, dry_run=dry_run)

    # Run custom package upgrades.
    reporting.heading("Upgrading custom packages")
    manual = upgrade_packages(configuration.packages, env=env, dry_run=dry_run)

    # Run maintenance scripts.
    reporting.heading("Running upgrade scripts")
    up_scripts = [script for script in configuration.scripts if script.name.startswith("up_")]
    run_scripts(up_scripts, env=env, dry_run=dry_run)

    # Present manual work only after automated maintenance finishes.
    if manual:
        reporting.warning("Manual upgrades required.")
        for package in manual:
            reporting.detail(package)

    reporting.plain("")
    reporting.success("Complete.")
