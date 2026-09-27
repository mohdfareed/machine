"""Deploy the selected machine configuration."""

from typing import Annotated

import typer

from app import cli
from app.config.discovery import list_machines
from app.config.loader import load_machine
from app.deployment.files import deploy_file
from app.deployment.managers import setup_managers
from app.deployment.packages import install_packages
from app.deployment.scripts import run_scripts
from app.runtime import reporting
from app.runtime.env import get_current_machine, save_machine

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Deploy Command
# ═════════════════════════════════════════════════════════════════════════════


def deploy(
    machine: Annotated[
        str | None,
        typer.Option(
            "-m",
            "--machine",
            metavar="MACHINE",
            help="The machine to set up.",
            autocompletion=cli.complete_machines,
            callback=cli.validate_machine,
            default_factory=get_current_machine,
        ),
    ],
    module_names: Annotated[
        list[str],
        typer.Argument(
            metavar="MODULES",
            help="Limit setup to the specified modules and their prerequisites.",
            autocompletion=cli.complete_modules,
        ),
    ] = [],
    dry_run: Annotated[
        bool, typer.Option("-n", "--dry-run", help="Preview changes without applying them.")
    ] = False,
) -> None:
    """Deploy configs, install packages, and run scripts."""
    if dry_run:
        reporting.detail("Dry run: no changes will be made.")

    # Prompt the user for a machine if none was provided.
    machine = cli.validate_machine(machine or reporting.prompt("Machine", list_machines()))
    if machine is None:
        raise ValueError("No machine selected.")

    # Resolve the configuration and environment.
    configuration = load_machine(machine, module_names)
    env = configuration.env

    # Summarize this invocation.
    reporting.heading(f"Machine [{machine}]")
    reporting.detail(f"Managers: {' | '.join(configuration.pkg_managers) or 'none'}")

    # Debug info.
    reporting.debug(f"Command: {deploy.__name__} ({'dry run' if dry_run else 'execute'})")
    reporting.debug(f"Modules: {', '.join(module_names) or 'all'}")
    reporting.debug(
        f"Inputs: "
        f"{len(configuration.modules)} modules, "
        f"{len(configuration.files)} files, "
        f"{len(configuration.scripts)} scripts, "
        f"{len(configuration.packages)} packages."
    )

    # Summarize modules
    reporting.heading("Modules")
    reporting.grid(configuration.modules)

    # Save the default machine and shell environment.
    if not dry_run:
        save_machine(machine, env)

    # Set up the platform's package managers.
    reporting.heading("Preparing package managers")
    setup_managers(configuration.pkg_managers, env=env, dry_run=dry_run)

    # Prepare the host before linking files or installing packages.
    reporting.heading("Running init scripts")
    init_scripts = [script for script in configuration.scripts if script.name.startswith("init_")]
    run_scripts(init_scripts, env=env, dry_run=dry_run)

    # Deploy files after initialization has prepared their prerequisites.
    reporting.heading("Deploying files")
    for mapping in configuration.files:
        deploy_file(mapping, env=env, dry_run=dry_run)

    # Install missing packages.
    reporting.heading("Installing packages")
    install_packages(configuration.packages, env=env, dry_run=dry_run)

    # Run the deployment scripts.
    reporting.heading("Running scripts")
    post_scripts = [
        script for script in configuration.scripts if not script.name.startswith(("init_", "up_"))
    ]
    run_scripts(post_scripts, env=env, dry_run=dry_run)

    reporting.plain("")
    reporting.success("Complete.")
