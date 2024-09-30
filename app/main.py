"""Main module for the Typer Machine Setup CLI."""

from typing import Annotated

import typer

APP_NAME = "machine-setup"
app = typer.Typer()


@app.command()
def setup(
    machine_name: Annotated[
        str, typer.Argument(help="The name of the machine to setup")
    ],
) -> None:
    """Machine setup CLI"""

    typer.echo(f"Setting up {machine_name}...")
    typer.echo(f"Machine path: {typer.get_app_dir(APP_NAME)}")
    typer.echo("Done!")
