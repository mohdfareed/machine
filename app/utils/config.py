"""Machine configuration utilities."""

__all__ = ["load_env"]

from pathlib import Path
from typing import TYPE_CHECKING, Optional, TypeVar

from dotenv import dotenv_values

from .filesystem import create_temp_file
from .logging import LOGGER
from .misc import UNIX
from .shell import Executable, Shell

# typechecking imports
if TYPE_CHECKING:
    from app import models


Env = TypeVar("Env", bound="models.Environment")
Config = TypeVar("Config", bound="models.ConfigFiles")


def load_env(model: Env, env_file: Path) -> Env:
    """Create an environment model from a file."""
    LOGGER.debug("Loading environment from: %s", env_file)
    env_vars = _load_env_vars(env_file)

    for field in model.model_fields:
        setattr(model, field, env_vars.get(field, getattr(model, field)))
    return model


def _load_env_vars(env_file: Path) -> dict[str, Optional[str]]:
    path = create_temp_file(env_file.name)
    shell = Shell()

    # load the environment variables into a file
    if UNIX and env_file.suffix in (".ps1", ".psm1"):
        shell.executable = Executable.PWSH
        cmd = (
            f'. "{env_file}" ; Get-ChildItem Env:* | ForEach-Object '
            f'{{ "$($_.Name)=$($_.Value)" }} | Out-File -FilePath "{path}"'
        )
        shell.executable = Executable.PWSH
    else:
        cmd = f"source '{env_file}' && env > '{path}'"
    shell.execute(cmd)

    # filter out unparsable environment variables
    def _filter(line: str) -> bool:
        return "=" in line

    # update the file in place and return the parsed environment variables
    contents = [line for line in path.read_text().split("\n") if _filter(line)]
    path.write_text("\n".join(contents))
    return dotenv_values(path)
