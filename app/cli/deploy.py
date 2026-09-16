"""Deploy the selected machine configuration."""

from pathlib import Path
from typing import Annotated

import typer
from rich.text import Text

from app import cli, reporting
from app import env as app_env
from app.discovery import list_machines
from app.env import build_env, get_current_machine, set_current_machine
from app.machine import load_machine
from app.managers import setup_managers, validate_managers
from app.ops.files import deploy_file
from app.ops.packages import install_packages
from app.ops.scripts import run_scripts

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

    # Load and validate the machine and its environment.
    env = build_env(machine)
    configuration = load_machine(machine, module_names, env=env)

    # Summarize this invocation before checking live prerequisites.
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

    # Save the default machine only after validation.
    validate_managers(configuration.pkg_managers, env=env)
    if not dry_run:
        set_current_machine(machine)

    # Deploy files and prepare the declared package managers.
    reporting.heading("Deploying files")
    for mapping in configuration.files:
        status = "Deployed" if deploy_file(mapping, env=env, dry_run=dry_run) else "Skipped"
        reporting.path(mapping.source, root=app_env.ROOT, prefix=f"{status}: ")

    # Set up the declared package managers.
    reporting.heading("Preparing package managers")
    setup_managers(configuration.pkg_managers, env=env, dry_run=dry_run)

    # Run initialization scripts before installing packages.
    reporting.heading(f"Running init scripts")
    for script in [
        script for script in configuration.scripts if Path(script).name.startswith("init_")
    ]:
        run_scripts([script], env=env, dry_run=dry_run)

    # Install missing packages.
    reporting.heading("Installing packages")
    install_packages(configuration.packages, env=env, dry_run=dry_run, reporter=reporting.detail)

    # Run the deployment scripts.
    reporting.heading("Running scripts")
    post_scripts = [
        script
        for script in configuration.scripts
        if not Path(script).name.startswith(("init_", "up_"))
    ]
    run_scripts(post_scripts, env=env, dry_run=dry_run)

    reporting.plain("")
    reporting.success("Complete.")
