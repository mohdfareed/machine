"""Main module for the Typer Machine Setup CLI."""

import logging
import platform
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.logging import RichHandler

from app import __version__, machines, plugins, utils

APP_NAME = "machine-setup"
app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    result_callback=utils.post_installation,
)
app.registered_groups += machines.app.registered_groups
app.add_typer(plugins.app)


@app.callback()
def main(
    debug_mode: Annotated[
        bool,
        typer.Option("--debug", "-d", help="Log debug messages to the console."),
    ] = False,
) -> None:
    """Machine setup CLI."""

    # debug logger
    debug = RichHandler(markup=True, show_path=False, show_time=False)
    debug.setFormatter(logging.Formatter(r"[black]%(message)s[/]"))
    debug.setLevel(logging.DEBUG)
    debug.addFilter(lambda msg: msg.levelno < logging.INFO if debug_mode else False)

    # stdout logger
    stdout = RichHandler(markup=True, show_path=False, show_time=False)
    stdout.setLevel(logging.INFO)
    stdout.addFilter(lambda msg: msg.levelno < logging.ERROR)

    # stderr logger
    console = Console(stderr=True)
    stderr = RichHandler(console=console, markup=True, show_path=False, show_time=False)
    stderr.setLevel(logging.ERROR)

    # setup file logger
    file_path = Path(__file__).parent.parent / "app.log"
    log_file = RotatingFileHandler(file_path, maxBytes=2**20, backupCount=5)
    log_file.setLevel(logging.NOTSET)
    log_file.setFormatter(
        logging.Formatter(
            r"[%(asctime)s.%(msecs)03d] %(levelname)-8s "
            r"%(message)s [%(filename)s:%(lineno)d]",
            datefmt=r"%Y-%m-%d %H:%M:%S",
        )
    )

    # configure logging
    logging.captureWarnings(True)
    utils.LOGGER.setLevel(logging.NOTSET)
    utils.LOGGER.handlers = [debug, stdout, stderr, log_file]

    # debug information
    utils.LOGGER.debug("Machine version: %s", __version__)
    utils.LOGGER.debug("Python version: %s", platform.python_version())
    utils.LOGGER.debug("Platform: %s", platform.platform())
    utils.LOGGER.debug("Log file: %s", log_file)
    utils.LOGGER.debug("Debug mode: %s", debug_mode)
    utils.LOGGER.debug("Windows: %s", utils.WINDOWS)
    utils.LOGGER.debug("macOS: %s", utils.MACOS)
    utils.LOGGER.debug("Linux: %s", utils.LINUX)
    utils.LOGGER.debug("ARM: %s", utils.ARM)
