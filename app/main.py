"""Main module for the Typer Machine Setup CLI."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import sleep
from typing import Annotated

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import track

from app import __version__, utils
from app.config import MachineConfig, UnixEnvironment, WindowsEnvironment

APP_NAME = "machine-setup"
LOGGER = logging.getLogger(APP_NAME)

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


@app.callback()
def main(
    debug_mode: Annotated[
        bool,
        typer.Option("--debug", "-d", help="Log debug messages to the console."),
    ] = False,
) -> None:
    """Machine setup CLI."""

    # stdout logger
    stdout = RichHandler(markup=True, show_path=False, show_time=False)
    stdout.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    stdout.addFilter(lambda record: record.levelno < logging.ERROR)

    # stderr logger
    stderr = RichHandler(
        console=Console(stderr=True), markup=True, show_path=False, show_time=False
    )
    stderr.setLevel(logging.ERROR)

    # setup file logger
    file_path = Path(__file__).parent.parent / "app.log"
    file = RotatingFileHandler(file_path, maxBytes=2**20, backupCount=5)
    file.setLevel(logging.NOTSET)
    file.setFormatter(
        logging.Formatter(
            r"[%(asctime)s.%(msecs)03d] %(levelname)-8s "
            r"%(message)s [%(filename)s:%(lineno)d]",
            datefmt=r"%Y-%m-%d %H:%M:%S",
        )
    )

    # configure logging
    logging.captureWarnings(True)
    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)
    logger.handlers = [stdout, stderr, file]

    # report app version
    LOGGER.debug("Machine app v%s", __version__)


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
    """Setup a machine with the provided name."""

    if machine_name.strip() == "":
        LOGGER.error("No machine name provided")
        raise typer.Abort()

    config_files = MachineConfig()
    win_env = WindowsEnvironment()
    unix_env = UnixEnvironment()

    LOGGER.info("Machine: %s", machine_name)
    LOGGER.debug("Config files: %s", config_files.model_dump_json(indent=2))

    if utils.WINDOWS:
        LOGGER.debug("Environment: %s", win_env.model_dump_json(indent=2))
    else:
        LOGGER.debug("Environment: %s", unix_env.model_dump_json(indent=2))

    LOGGER.info("Setting up machine...")
    for _ in track(range(15), description="Processing...", transient=True):
        sleep(0.1)

    LOGGER.info("Machine setup completed successfully")
    raise typer.Exit()
