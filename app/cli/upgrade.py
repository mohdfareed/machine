"""Upgrade packages and run maintenance for the selected machine."""

from pathlib import Path
from typing import Annotated

import typer

from app import cli, reporting
from app.env import build_env, get_current_machine
from app.machine import load_machine
from app.managers import upgrade_managers, validate_managers
from app.ops.packages import upgrade_packages
from app.ops.scripts import run_scripts

# =============================================================================
# MARK: Upgrade Command
# =============================================================================


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
    """Upgrade declared managers globally, then run selected custom maintenance."""
    if dry_run:
        reporting.heading("Dry run: no changes will be made.")

    # Prepare the selected configuration and check installed managers before upgrades.
    machine_id = get_current_machine()
    if not machine_id:
        raise ValueError(f"No machine selected. Select one with {cli.COMMAND} deploy.")
    env = build_env(machine_id)
    configuration = load_machine(machine_id, module_names, env=env)
    validate_managers(configuration.pkg_managers, env=env, for_upgrade=True)
    reporting.heading(machine_id)

    # Upgrade all packages owned by the declared managers.
    reporting.heading("Upgrading declared managers and all their packages")
    upgrade_managers(configuration.pkg_managers, env=env, dry_run=dry_run)

    # Run custom package upgrades and maintenance scripts for the selected modules.
    reporting.heading("Upgrading custom packages")
    manual = upgrade_packages(configuration.packages, env=env, dry_run=dry_run)
    up_scripts = [script for script in configuration.scripts if Path(script).name.startswith("up_")]
    reporting.heading("Running upgrade scripts")
    run_scripts(up_scripts, env=env, dry_run=dry_run)

    # Present manual work only after automated maintenance finishes.
    if manual:
        reporting.warning("Manual upgrades required.")
        for package in manual:
            reporting.detail(package)

    reporting.success("Complete.")
