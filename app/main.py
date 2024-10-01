"""Main module for the Typer Machine Setup CLI."""

import time
from typing import Annotated

import typer
from rich.progress import track
from rich.status import Status

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

    typer.echo(f"Setting up {machine_name}...")
    typer.echo(f"Machine path: {typer.get_app_dir(APP_NAME)}")

    for _ in track(range(25), description="Downloading files"):
        time.sleep(0.1)

    with Status("Setting up...") as status:
        time.sleep(0.5)
        status.update("Setting up configuration files...")
        time.sleep(0.5)
        status.update("Setting up environment variables...")
        time.sleep(0.5)

    typer.echo("Machine setup completed successfully")
    raise typer.Exit()
