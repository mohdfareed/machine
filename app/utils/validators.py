"""CLI arguments validators."""

__all__ = [
    "validate",
    "is_optional",
    "is_path",
    "is_dir",
    "is_file",
]

from pathlib import Path
from typing import Callable, TypeVar

import typer

T = TypeVar("T")


class SkipValidation(Exception):
    """Skip validation exception."""


def validate(*validators: Callable[[T], T]) -> Callable[[T], T]:
    """Validate data against a list of validators."""

    def validator(data: T) -> T:
        for _validator in validators:
            try:
                data = _validator(data)
            except SkipValidation:
                break
        return data

    return validator


def is_optional(value: T) -> T:
    """Validate that a value is optional."""
    if value is None:
        raise SkipValidation("Value is optional")
    return value


def is_path(path: Path) -> Path:
    """Validate that a path exists."""
    if path.exists():
        return path
    raise typer.BadParameter(f"Path does not exist: {path}")


def is_dir(path: Path) -> Path:
    """Validate that a path exists and is a directory."""
    if path.exists() and path.is_dir():
        return path
    raise typer.BadParameter(f"Path is not a directory: {path}")


def is_file(path: Path) -> Path:
    """Validate that a path exists and is a file."""
    if path.exists() and path.is_file():
        return path
    raise typer.BadParameter(f"Path is not a file: {path}")
