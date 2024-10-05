"""Main module for the Typer Machine Setup CLI."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.logging import RichHandler

from app import __version__
from app.machines import testing
from app.plugins import private_files
from app.utils import LOGGER

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(testing.app)
app.add_typer(private_files.app)


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
    LOGGER.setLevel(logging.NOTSET)
    LOGGER.handlers = [stdout, stderr, file]

    # report app version
    LOGGER.debug("Machine app v%s", __version__)
