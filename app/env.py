"""Environment variables models."""

import getpass
import shutil
import subprocess
from abc import ABC
from pathlib import Path
from typing import Optional, Type, TypeVar

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

    @classmethod
    def os_env(cls) -> "type[Environment]":
        """Load environment variables from the current environment."""
        return Windows if utils.WINDOWS else Unix

    @classmethod
    def load(
        cls: Type[T],
        env: Optional[Path] = None,
        pwsh: Optional[bool] = None,
    ) -> T:
        """Load environment variables from a file."""
        if env is None:
            env = (
                config.Default().ps_profile
                if utils.WINDOWS
                else config.Default().zshenv
            )

        temp_file = utils.create_temp_file(env.name)
        env_vars = _load_env(temp_file, issubclass(cls, Windows), env, pwsh)
        utils.LOGGER.debug("Loaded environment variables from: %s", env)

        env_instance = cls()
        for field in env_instance.model_fields:
            if field in env_vars:
                setattr(env_instance, field, env_vars[field])
        return env_instance


class Unix(Environment):
    """Unix environment variables."""

    XDG_CONFIG_HOME: Path = Path.home() / ".config"
    XDG_DATA_HOME: Path = Path.home() / ".local/share"
    COMPLETIONS_PATH: Optional[Path] = None

    GITCONFIG: Path = XDG_CONFIG_HOME / "git" / "config"
    GITIGNORE: Path = XDG_CONFIG_HOME / "git" / "ignore"


class Windows(Environment):
    """Windows environment variables."""

    APPDATA: Path = Path.home() / "AppData" / "Roaming"
    LOCALAPPDATA: Path = Path.home() / "AppData" / "Local"
    USERPROFILE: Path = Path.home() / "User" / getpass.getuser()

    GITCONFIG: Path = USERPROFILE / ".gitconfig"
    GITIGNORE: Path = USERPROFILE / ".gitignore"


def _load_env(
    path: Path,
    is_windows: bool,
    env: Path,
    pwsh: Optional[bool] = None,
) -> dict[str, Optional[str]]:

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

    # filter out file
    with open(path, "r+", encoding="utf-8") as file:
        lines = file.readlines()
        # remove lines not in the form of KEY=VALUE
        lines = [line for line in lines if "=" in line]
        # remove variables in the form _=VALUE
        lines = [line for line in lines if not line.startswith("_=")]
        # update file
        file.seek(0)
        file.writelines(lines)
        file.truncate()

    return dotenv_values(path)
