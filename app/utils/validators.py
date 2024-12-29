"""CLI arguments validators."""

__all__ = [
    "validate",
    "path_exists",
    "is_dir",
    "is_file",
    "FileArg",
    "OptionalFileArg",
    "DirArg",
    "OptionalDirArg",
    "PathArg",
    "OptionalPathArg",
]

from pathlib import Path
from typing import Annotated, Callable, Optional, TypeVar

import typer

T = TypeVar("T")


def validate(*validators: Callable[[T], T]) -> Callable[[T], T]:
    """Validate data against a list of validators."""

    def validator(data: T) -> T:
        for _validator in validators:
            data = _validator(data)
        return data

    return validator


def path_exists(path: Optional[Path]) -> Optional[Path]:
    """Validate that a path exists."""
    if not path or path.exists():
        return path  # allow None through
    raise typer.BadParameter(f"Path does not exist: {path}")


def is_dir(path: Optional[Path]) -> Optional[Path]:
    """Validate that a path is a directory."""
    if not path or path.is_dir():
        return path  # allow None through
    raise typer.BadParameter(f"Path is not a directory: {path}")


def is_file(path: Optional[Path]) -> Optional[Path]:
    """Validate that a path is a file."""
    if not path or path.is_file():
        return path  # allow None through
    raise typer.BadParameter(f"Path is not a file: {path}")


FileArg = Annotated[Path, typer.Argument(callback=validate(is_file))]
OptionalFileArg = Annotated[Optional[Path], typer.Argument(callback=validate(is_file))]

DirArg = Annotated[Path, typer.Argument(callback=validate(is_dir))]
OptionalDirArg = Annotated[Optional[Path], typer.Argument(callback=validate(is_dir))]

PathArg = Annotated[Path, typer.Argument(callback=validate(path_exists))]
OptionalPathArg = Annotated[
    Optional[Path], typer.Argument(callback=validate(path_exists))
]
