"""Environment variables models."""

import shutil
import subprocess
from abc import ABC
from pathlib import Path
from typing import Annotated, Optional, TypeVar

from dotenv import dotenv_values
from pydantic_settings import BaseSettings, SettingsConfigDict

from app import config, utils

T = TypeVar("T", bound="Environment")


class Environment(BaseSettings, ABC):
    """Environment variables."""

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    MACHINE: Path = Path(__file__).parent.parent
    GITCONFIG: Path = Path.home() / ".gitconfig"
    GITIGNORE: Path = Path.home() / ".gitignore"

    def load(
        self: T,
        env: Optional[Path] = None,
        pwsh: Optional[bool] = None,
    ) -> T:
        """Load environment variables from a file."""
        env_vars = _load_env(isinstance(self, Windows), env, pwsh)
        utils.LOGGER.debug("Loaded environment variables from: %s", env)
        for field in self.model_fields:
            if field in env_vars:
                setattr(self, field, env_vars[field])
        return self


class Unix(Environment):
    """Unix environment variables."""

    XDG_CONFIG_HOME: Path = Path.home() / ".config"
    XDG_DATA_HOME: Path = Path.home() / ".local/share"
    COMPLETIONS_PATH: Optional[Path] = None

    GITCONFIG: Path = XDG_CONFIG_HOME / "git" / "config"
    GITIGNORE: Path = XDG_CONFIG_HOME / "git" / "ignore"


class Windows(Environment):
    """Windows environment variables."""

    USERPROFILE: Path = Path.home()
    APPDATA: Path = Path.home() / "AppData" / "Roaming"
    LOCALAPPDATA: Path = Path.home() / "AppData" / "Local"

    GITCONFIG: Path = USERPROFILE / ".gitconfig"
    GITIGNORE: Path = USERPROFILE / ".gitignore"


EnvArg = Annotated[Environment, utils.IgnoredArgument]
OSEnv = Windows if utils.WINDOWS else Unix


def _load_env(
    is_windows: bool,
    env: Optional[Path],
    pwsh: Optional[bool] = None,
) -> dict[str, Optional[str]]:

    if env is None:
        env = config.Default().ps_profile if utils.WINDOWS else config.Default().zshenv
    path = utils.create_temp_file(env.name)

    if pwsh or (pwsh is None and is_windows):
        executable = shutil.which("pwsh") or shutil.which("powershell")
        cmd = (
            f'. "{env}" ; Get-ChildItem Env:* | ForEach-Object '
            f'{{ "$($_.Name)=$($_.Value)" }} | Out-File -FilePath "{path}"'
        )

    else:
        executable = shutil.which("zsh") or shutil.which("bash") or shutil.which("sh")
        cmd = f"source '{env}' && env > '{path}'"

    result = subprocess.run(
        cmd,
        text=True,
        shell=True,
        check=False,
        capture_output=True,
        executable=executable,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to execute command: {result.stderr}")

    # filter out empty lines and comments
    with open(path, "r+", encoding="utf-8") as file:
        lines = file.readlines()
        lines = [line for line in lines if "=" in line]
        lines = [line for line in lines if not line.startswith("_=")]

        # update file
        file.seek(0)
        file.writelines(lines)
        file.truncate()
    return dotenv_values(path)
