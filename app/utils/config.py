"""Machine configuration utilities."""

__all__ = ["load_env"]

from pathlib import Path
from typing import TYPE_CHECKING, Optional, TypeVar

from dotenv import dotenv_values

from .filesystem import create_temp_file
from .logging import LOGGER
from .shell import OS_EXECUTABLE, Executable, Shell

# typechecking imports
if TYPE_CHECKING:
    from app import models


Env = TypeVar("Env", bound="models.Environment")
Config = TypeVar("Config", bound="models.ConfigFiles")


def load_env(model: Env, env_file: Path, executable: Optional[Executable]) -> Env:
    """Create an environment model from a file."""
    LOGGER.debug("Loading environment from: %s", env_file)
    env_vars = _load_env_vars(env_file, executable)

    for field in model.model_fields:
        setattr(model, field, env_vars.get(field, getattr(model, field)))
    return model


def _load_env_vars(
    env_file: Path, executable: Optional[Executable]
) -> dict[str, Optional[str]]:
    path = create_temp_file()
    shell = Shell(executable or OS_EXECUTABLE)

    # ensure correct extension for powershell
    if executable == Executable.PWSH and env_file.suffix != ".ps1":
        env_contents = env_file.read_text()
        env_file = create_temp_file(env_file.with_suffix(".ps1").name)
        env_file.write_text(env_contents)

    # load the environment variables into a file
    if env_file.suffix == ".ps1":
        cmd = (
            f'. "{env_file}" ; Get-ChildItem env:* | ForEach-Object '
            f'{{ "$($_.Name)=$($_.Value)" }} | Out-File -FilePath "{path}" ;'
        )

        if executable != Executable.PWSH:
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
