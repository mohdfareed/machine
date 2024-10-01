"""Machine configuration models."""

import os
from pathlib import Path
from typing import Optional

import pydantic

CONFIG_PATH: Path = Path(__file__).parent.parent / "config"
"""Machine configuration files path."""


class Config(pydantic.BaseModel):
    """Machine Configuration model."""


class ConfigFiles(Config):
    """Machine configuration files."""

    vim: Path = CONFIG_PATH / "vim"
    vscode: Path = CONFIG_PATH / "vscode"
    gitconfig: Path = CONFIG_PATH / ".gitconfig"
    gitignore: Path = CONFIG_PATH / ".gitignore"
    ps_profile: Path = CONFIG_PATH / "ps_profile.ps1"
    tmux: Path = CONFIG_PATH / "tmux.conf"
    zed_settings: Path = CONFIG_PATH / "zed_settings.jsonc"
    zshrc: Path = CONFIG_PATH / "zshrc"
    zshenv: Path = CONFIG_PATH / "zshenv"


class Environment(Config):
    """Machine environment variables."""

    MACHINE: Path = Path.home() / ".machine"
    PRIVATE_ENV: Optional[Path] = None
    SSH_KEYS: Optional[Path] = None


class WindowsVariables(Config):
    """Windows environment variables."""

    LOCALAPPDATA: Path = pydantic.Field(
        default_factory=lambda: Path(os.environ["LOCALAPPDATA"]),
    )
    APPDATA: Path = pydantic.Field(
        default_factory=lambda: Path(os.environ["APPDATA"]),
    )


class UnixVariables(Config):
    """Unix environment variables."""

    XDG_CONFIG_HOME: Path = Path.home() / ".config"
    XDG_DATA_HOME: Path = Path.home() / ".local" / "share"
    COMPLETIONS_PATH: Optional[Path] = None
