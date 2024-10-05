"""Main module for the Typer Machine Setup CLI."""

import atexit
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

    log_file = setup_logging(debug_mode)
    atexit.register(post_installation)

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


def post_installation() -> None:
    """Run post installation tasks."""

    utils.LOGGER.info("[bold green]Running post installation tasks...[/]")
    for post_installation_task in utils.post_installation:
        post_installation_task()


def setup_logging(debug_mode: bool) -> Path:
    """Setup file and console logging. Return the log file path."""

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
    utils.LOGGER.setLevel(logging.NOTSET)
    utils.LOGGER.handlers = [debug, stdout, stderr, file]
    return file_path
