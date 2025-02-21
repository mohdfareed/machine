"""Filesystem utilities."""

__all__ = ["link", "create_temp_dir", "create_temp_file", "load_env_vars"]

import atexit
import shutil
import uuid
from pathlib import Path
from typing import Optional

import typer
from dotenv import dotenv_values

from app import APP_NAME

from .logging import LOGGER
from .shell import OS_EXECUTABLE, Executable, Shell


def link(source: Path, target: Path) -> None:
    """Link files and directories from source to target."""

    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        for file in source.iterdir():
            link(source=file, target=target / file.name)
        return

    target.unlink(missing_ok=True)
    target.symlink_to(source, target_is_directory=target.is_dir())
    LOGGER.debug("Linked: %s => %s", target, source)


def create_temp_dir() -> Path:
    """Create a temporary directory."""

    temp_dir = Path(typer.get_app_dir(APP_NAME)) / f"{uuid.uuid4()}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    atexit.register(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
    return temp_dir


def create_temp_file(suffix: str = "") -> Path:
    """Create a temporary file."""

    temp_file = Path(typer.get_app_dir(APP_NAME)) / f"{uuid.uuid4()}{suffix}"
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    atexit.register(lambda: temp_file.unlink(missing_ok=True))
    return temp_file


def load_env_vars(env_file: Path) -> dict[str, Optional[str]]:
    """Load the environment variables from a file."""

    shell = Shell(
        Executable.PWSH if env_file.suffix == ".ps1" else OS_EXECUTABLE
    )
    suffix = ".ps1" if shell.executable == Executable.PWSH else env_file.suffix
    env_data = env_file.read_text()

    env_file = create_temp_file(suffix)
    env_file.write_text(env_data)
    gen_env_file = create_temp_file(".env")

    # load the environment variables into a file
    if env_file.suffix == ".ps1":
        cmd = (
            f'. "{env_file}" ; Get-ChildItem env:* | '
            f'ForEach-Object {{ "$($_.Name)=$($_.Value)" }} | '
            f'Out-File -FilePath "{gen_env_file}" ;'
        )
    else:
        cmd = f"source '{env_file}' && env > '{gen_env_file}'"
    shell.execute(cmd)

    # filter out invalid environment variables
    gen_env_file.write_text(
        "\n".join(
            filter(
                lambda l: "=" in l,  # invalid assignment
                gen_env_file.read_text().splitlines(),
            )
        )
    )

    return dotenv_values(gen_env_file)
