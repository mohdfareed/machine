"""Filesystem utilities."""

__all__ = ["link", "create_temp_dir", "create_temp_file"]

import atexit
import shutil
import uuid
from pathlib import Path

import typer

from app import APP_NAME

from .logging import LOGGER


def link(source: Path, target: Path) -> None:
    """Link files and directories from source to target."""

    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    target.symlink_to(source, target_is_directory=source.is_dir())
    LOGGER.debug("Linked: %s => %s", target, source)


def create_temp_dir(name: str = "") -> Path:
    """Create a temporary directory."""

    temp_file = Path(typer.get_app_dir(APP_NAME)) / f"{name}.{uuid.uuid4()}"
    temp_file.mkdir(parents=True, exist_ok=True)
    atexit.register(lambda: shutil.rmtree(temp_file, ignore_errors=True))
    return temp_file


def create_temp_file(name: str = "") -> Path:
    """Create a temporary file."""

    temp_file = Path(typer.get_app_dir(APP_NAME)) / f"{name}-{uuid.uuid4()}"
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    atexit.register(lambda: temp_file.unlink(missing_ok=True))
    return temp_file
