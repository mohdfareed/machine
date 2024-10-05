"""Environment variables models."""

import getpass
import shutil
import subprocess
from abc import ABC
from pathlib import Path
from typing import Optional

import typer
from pydantic_settings import BaseSettings, SettingsConfigDict

from app import APP_NAME, utils


class Environment(BaseSettings, ABC):
    """Environment variables."""

    model_config = SettingsConfigDict()

    GITCONFIG: Path = Path.home() / ".gitconfig"
    GITIGNORE: Path = Path.home() / ".gitignore"

    @classmethod
    def os_env(cls) -> "Environment":
        """Load environment variables from the current environment."""
        return Windows() if utils.WINDOWS else Unix()

    @classmethod
    def load(
        cls, env: Optional[Path] = None, pwsh: Optional[bool] = None
    ) -> "Environment":
        """Load environment variables from a file.

        Args:
            env (str, optional): Path to the environment file.
                Defaults to loading the current environment.
            pwsh (bool, optional): Use PowerShell if True, use bash/zsh if False.
                Defaults to None (auto-detect based on OS).
        """
        if not env:
            return cls()

        temp_file = Path(typer.get_app_dir(APP_NAME)) / env.name
        temp_file.mkdir(parents=True, exist_ok=True)

        if pwsh or (pwsh is None and issubclass(cls, Windows)):
            executable = shutil.which("pwsh") or shutil.which("powershell")
            cmd = f'. {env} ; Get-ChildItem Env:* | ForEach-Object { "$($_.Name)=$($_.Value)" } | Out-File -FilePath {temp_file}'
        else:
            executable = (
                shutil.which("zsh") or shutil.which("bash") or shutil.which("sh")
            )
            cmd = f"source {env} && env > {temp_file}"

        result = subprocess.run(
            cmd,
            executable=executable,
            text=True,
            shell=True,
            check=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to execute PowerShell command: {result.stderr}")

        env_instance = cls(_env_file=temp_file)  # type: ignore
        temp_file.unlink()
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
