"""Main module for the Typer Machine Setup CLI."""

from typing import Annotated

import typer

from app import utils
from app.config import ConfigFiles, UnixEnvironment, WindowsEnvironment

APP_NAME = "machine-setup"
app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})

# TODO: Add method to add warnings, messages, errors, to report at the end of the script.


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
    win_env = WindowsEnvironment()
    unix_env = UnixEnvironment()

    typer.echo(f"Machine: {machine_name}")
    typer.echo(f"Config files: {config_files.model_dump_json(indent=2)}")

    if utils.is_windows:
        typer.echo(f"Environment: {win_env.model_dump_json(indent=2)}")
    else:
        typer.echo(f"Environment: {unix_env.model_dump_json(indent=2)}")

    typer.echo("Machine setup completed successfully")
    raise typer.Exit()
