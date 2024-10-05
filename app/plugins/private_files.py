"""Plugin for setting up private files on a machine."""

from pathlib import Path
from typing import Annotated

import typer

from app import config, utils

app: typer.Typer = typer.Typer(name="private")


@app.callback(invoke_without_command=True)
def setup(
    private_env: Annotated[
        Path,
        typer.Argument(
            help="The private environment file.",
            callback=utils.validate_file,
        ),
    ],
    ssh_keys: Annotated[
        Path,
        typer.Argument(
            help="The SSH keys directory.",
            callback=utils.validate_dir,
        ),
    ],
) -> None:
    """Setup private files on a machine."""
    utils.LOGGER.info("Setting up private files...")
    machine_config = config.MachineConfig()
    utils.link(private_env, machine_config.private_env)
    utils.link(ssh_keys, machine_config.ssh_keys)
    utils.LOGGER.info("Private files setup complete")
