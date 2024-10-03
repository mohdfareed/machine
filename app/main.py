"""Main module for the Typer Machine Setup CLI."""

from time import sleep
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import track

from app import utils
from app.config import MachineConfig, UnixEnvironment, WindowsEnvironment

APP_NAME = "machine-setup"
app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})

# replace with logging module
reports: list[str] = []  # post setup reports generated by the setup process
stderr = Console(stderr=True, record=True)
stdout = Console(record=True)


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

    if machine_name.strip() == "":
        stderr.print("No machine name provided")
        raise typer.Abort()

    config_files = MachineConfig()
    win_env = WindowsEnvironment()
    unix_env = UnixEnvironment()

    stdout.print(f"Machine: {machine_name}")
    stdout.print(f"Config files: {config_files.model_dump_json(indent=2)}")
    stdout.print()

    if utils.WINDOWS:
        stdout.print(f"Environment: {win_env.model_dump_json(indent=2)}")
    else:
        stdout.print(f"Environment: {unix_env.model_dump_json(indent=2)}")
    stdout.print()

    stdout.print("Setting up machine...")
    for _ in track(range(25), description="Processing...", transient=True):
        sleep(0.1)

    if reports:  # display reports post setup
        stdout.print("Setup reports:")
        for report in reports:
            stdout.print(report)

    stdout.print("Machine setup completed successfully")
    raise typer.Exit()
