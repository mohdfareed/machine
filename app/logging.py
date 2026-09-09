"""Shared consoles and logging setup."""

import logging
import sys
from logging.handlers import RotatingFileHandler

from rich.console import Console
from rich.logging import RichHandler

from app.env import settings

_logger = logging.getLogger(__name__)
_output_logger = logging.getLogger(__name__ + ".output")
_console_handler: logging.Handler | None = None

# Output consoles
console = Console()
err_console = Console(stderr=True)


# =============================================================================
# MARK: Logging
# =============================================================================


# Route streamed subprocess output to the file only, never to the console.
_output_logger.propagate = False


def setup_console_logging() -> None:
    """Configure console logging with plain message text."""
    global _console_handler

    # Configure console detail from the debug setting.
    level = logging.DEBUG if settings.debug else logging.WARNING
    handler = RichHandler(
        level=level,
        console=err_console,
        show_time=settings.debug,
        show_path=settings.debug,
        rich_tracebacks=settings.debug,
        markup=False,
        keywords=[],
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    # Keep debug records available to the file handler.
    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(handler)
    _console_handler = handler


def setup_file_logging() -> None:
    """Configure rotating file logging."""
    # Create the rotating log file handler.
    log_file = settings.log_file
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler.setLevel(logging.DEBUG)

    # Share the file handler with application and subprocess output loggers.
    logging.root.addHandler(handler)
    _output_logger.addHandler(handler)

    # Separate invocations in the log file.
    _logger.debug("=" * 60)
    _logger.debug("mc %s", " ".join(sys.argv[1:]) or "(no args)")
    _logger.debug("=" * 60)
