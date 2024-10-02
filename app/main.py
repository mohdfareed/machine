"""Main module for the Typer Machine Setup CLI."""

from typing import Annotated

import typer

from app.config import ConfigFiles
from app.env import Machine, Unix

APP_NAME = "machine-setup"
app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


@app.command()
def setup(
    machine_name: Annotated[
        str,
        typer.Argument(
            envvar="MACHINE_NAME",
            help="The name of the machine to setup",
            default_factory=lambda: typer.prompt("Machine name"),
        ),
    ]
) -> None:
    """Machine setup CLI"""

    if machine_name == "":
        typer.echo("No machine name provided")
        raise typer.Abort()

    config_files = ConfigFiles()
    environment = Machine()
    machine_env = Unix()

    typer.echo(f"Machine: {machine_name}")
    typer.echo(f"Config files: {config_files.model_dump_json(indent=2)}")
    typer.echo(f"Environment: {environment.model_dump_json(indent=2)}")
    typer.echo(f"Machine env: {machine_env.model_dump_json(indent=2)}")

    typer.echo("Machine setup completed successfully")
    raise typer.Exit()
