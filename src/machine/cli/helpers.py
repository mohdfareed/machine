"""CLI helpers: logging and display utilities."""

__all__ = [
    "format_config",
    "setup_console_logging",
    "setup_file_logging",
]

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

from machine.config import app_settings


def setup_console_logging() -> None:
    """Configure `rich` console logging."""
    from . import err_console

    level = logging.DEBUG if app_settings.debug else logging.INFO
    handler = RichHandler(
        level=level,
        console=err_console,
        show_time=app_settings.debug,
        show_path=app_settings.debug,
        rich_tracebacks=True,
        markup=True,
        keywords=[],
    )

    handler.setFormatter(logging.Formatter("[dim]%(name)s:[/] %(message)s"))
    logging.root.setLevel(level)
    logging.root.addHandler(handler)


def setup_file_logging(log_file: Path) -> None:
    """Configure rotating file logging."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )

    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    file_handler.setLevel(logging.DEBUG)
    logging.root.addHandler(file_handler)

    # Stamp session separator
    session_logger = logging.getLogger(f"{app_settings.name}.session")
    session_logger.addHandler(file_handler)
    session_logger.setLevel(logging.INFO)
    session_logger.propagate = False
    session_logger.info("--- New Session ---")


def format_config(data: dict) -> list[str]:
    """Format a config dict into aligned Rich-markup lines."""
    lines: list[str] = []

    scalars: list[tuple[str, str]] = []
    sections: list[tuple[str, list[tuple[str, str]]]] = []

    for key, value in data.items():
        if isinstance(value, dict):
            items = [(k, str(v)) for k, v in value.items()]
            if items:
                sections.append((key, items))
        else:
            scalars.append((key, str(value)))

    if scalars:
        w = max(len(k) for k, _ in scalars)
        lines += [f"[dim]{k:<{w}}[/]  {v}" for k, v in scalars]

    for section, items in sections:
        lines.append(f"[dim]{section}:[/]")
        w = max(len(k) for k, _ in items)
        lines += [f"  [dim]{k:<{w}}[/]  {v}" for k, v in items]

    return lines
