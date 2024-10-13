"""CLI arguments validators."""

__all__ = [
    "validate",
    "is_path",
    "is_dir",
    "is_file",
    "FileArg",
    "OptionalFileArg",
    "ReqFileArg",
    "DirArg",
    "OptionalDirArg",
    "ReqDirArg",
    "ReqPathArg",
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


def is_path(path: Path) -> Path:
    """Validate that a path exists."""
    if not path or path.exists():
        return path  # allow None through
    raise typer.BadParameter(f"Path does not exist: {path}")


def is_dir(path: Path) -> Path:
    """Validate that a path exists and is a directory."""
    if not path or path.is_dir():
        return path  # allow None through
    raise typer.BadParameter(f"Path is not a directory: {path}")


def is_file(path: Path) -> Path:
    """Validate that a path exists and is a file."""
    if not path or path.is_file():
        return path  # allow None through
    raise typer.BadParameter(f"Path is not a file: {path}")


FileArg = Annotated[Path, typer.Argument(callback=validate(is_file))]
OptionalFileArg = Annotated[Optional[Path], typer.Argument(callback=validate(is_file))]
ReqFileArg = Annotated[Path, typer.Argument(callback=validate(is_path, is_file))]

DirArg = Annotated[Path, typer.Argument(callback=validate(is_dir))]
OptionalDirArg = Annotated[Optional[Path], typer.Argument(callback=validate(is_dir))]
ReqDirArg = Annotated[Path, typer.Argument(callback=validate(is_path, is_dir))]

ReqPathArg = Annotated[Path, typer.Argument(callback=validate(is_path))]
OptionalPathArg = Annotated[Optional[Path], typer.Argument(callback=validate(is_path))]
