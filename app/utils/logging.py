"""Logging setup module."""

__all__ = ["LOGGER", "init_logging"]

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

from app import APP_NAME

LOGGER = logging.getLogger(APP_NAME)
"""App logger."""

log_file_path = Path(__file__).parent.parent.parent / "app.log"
"""Log file path."""


class StripMarkupFilter(logging.Filter):  # pylint: disable=too-few-public-methods
    """Strip Rich markup from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter the log record message."""
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = Text.from_markup(record.msg).plain
        return True


def init_logging(debug_mode: bool) -> None:
    """Set up and initialize app logging."""

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
    log_file = RotatingFileHandler(log_file_path, maxBytes=2**20, backupCount=3)
    log_file.addFilter(StripMarkupFilter())
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
    logging.getLogger().setLevel(logging.NOTSET)
    logging.getLogger().handlers = [debug, stdout, stderr, log_file]
