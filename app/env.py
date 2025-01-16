"""Environment variables models."""

__all__ = ["MachineEnv", "Unix", "MacOS", "Windows", "OS_ENV"]

from abc import ABC
from pathlib import Path
from typing import Any, Optional

import platformdirs
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

from app import utils


class MachineEnv(BaseSettings, ABC):
    """Default machine environment variables."""

    env_file: Optional[Path] = None
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")
    SSH_DIR: Path = Path.home() / ".ssh"

    def __init__(self, env_file: Optional[Path] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.env_file = env_file
        self.load()

    def load(self) -> Self:
        """Load the environment variables from file."""
        if not self.env_file:
            return self

        utils.LOGGER.debug("Loading environment from: %s", self.env_file)
        env_vars = utils.load_env_vars(self.env_file)
        for field in self.model_fields:
            setattr(self, field, env_vars.get(field, getattr(self, field)))
        return self


class Unix(MachineEnv):
    """Unix environment variables."""

    XDG_CONFIG_HOME: Path = platformdirs.user_config_path()
    XDG_DATA_HOME: Path = platformdirs.user_data_path()
    COMPLETIONS_PATH: Path = XDG_DATA_HOME / "zinit" / "completions"
    ZDOTDIR: Path = XDG_CONFIG_HOME / "zsh"

    GITCONFIG: Path = XDG_CONFIG_HOME / "git" / "config"
    GITIGNORE: Path = XDG_CONFIG_HOME / "git" / "ignore"
    VSCODE: Path = platformdirs.user_config_path() / "Code" / "User"

    VIM: Path = XDG_CONFIG_HOME / "nvim"
    TMUX_CONFIG: Path = XDG_CONFIG_HOME / "tmux" / "tmux.conf"
    PS_PROFILE: Path = XDG_CONFIG_HOME / "powershell" / "profile.ps1"
    ZSHRC: Path = ZDOTDIR / ".zshrc"
    ZSHENV: Path = Path.home() / ".zshenv"
    ZED_SETTINGS: Path = XDG_CONFIG_HOME / "zed" / "settings.json"


class MacOS(Unix):
    """MacOS environment variables."""

    ICLOUD: Path = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
    GHOSTTY: Path = Unix().XDG_CONFIG_HOME / "ghostty" / "config.json"


class Windows(MachineEnv):
    """Windows environment variables."""

    USERPROFILE: Path = Path.home()
    APPDATA: Path = platformdirs.user_data_path(roaming=True)
    LOCALAPPDATA: Path = platformdirs.user_data_path()

    GITCONFIG: Path = USERPROFILE / ".gitconfig"
    GITIGNORE: Path = USERPROFILE / ".gitignore"
    VIM: Path = LOCALAPPDATA / "nvim"
    PS_PROFILE: Path = USERPROFILE / "Documents" / "WindowsPowerShell" / "profile.ps1"
    VSCODE: Path = APPDATA / "Code" / "User"

    COMPLETIONS_PATH: Optional[Path] = None


OS_ENV = Unix if utils.UNIX else Windows if utils.WINDOWS else MacOS
