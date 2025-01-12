"""Environment variables models."""

from abc import ABC
from pathlib import Path

import platformdirs
from pydantic_settings import BaseSettings, SettingsConfigDict

from app import utils


class Machine(BaseSettings, ABC):
    """Default machine environment variables."""

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")
    SSH_DIR: Path = Path.home() / ".ssh"

    def load(self, env_file: Path) -> None:
        """Load the environment variables from file."""
        utils.LOGGER.debug("Loading environment from: %s", env_file)

        env_vars = utils.load_env_vars(env_file)
        for field in self.model_fields:
            setattr(self, field, env_vars.get(field, getattr(self, field)))


class Unix(Machine):
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


class Windows(Machine):
    """Windows environment variables."""

    USERPROFILE: Path = Path.home()
    APPDATA: Path = platformdirs.user_data_path(roaming=True)
    LOCALAPPDATA: Path = platformdirs.user_data_path()

    GITCONFIG: Path = USERPROFILE / ".gitconfig"
    GITIGNORE: Path = USERPROFILE / ".gitignore"
    VIM: Path = LOCALAPPDATA / "nvim"
    PS_PROFILE: Path = USERPROFILE / "Documents" / "WindowsPowerShell" / "profile.ps1"
    VSCODE: Path = APPDATA / "Code" / "User"
