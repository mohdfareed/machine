"""Machine configuration models."""

import os
from pathlib import Path
from typing import Optional

import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Machine Configuration model."""

    model_config = SettingsConfigDict()


class ConfigFiles(Config):
    """Machine configuration files."""

    config_path: Path = Path(__file__).parent.parent / "config"
    vim: Path = config_path / "vim"
    vscode: Path = config_path / "vscode"
    gitconfig: Path = config_path / ".gitconfig"
    gitignore: Path = config_path / ".gitignore"
    ps_profile: Path = config_path / "ps_profile.ps1"
    tmux: Path = config_path / "tmux.conf"
    zed_settings: Path = config_path / "zed_settings.jsonc"
    zshrc: Path = config_path / "zshrc"
    zshenv: Path = config_path / "zshenv"


class Environment(Config):
    """Machine environment variables."""

    MACHINE: Path
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

    XDG_CONFIG_HOME: Path
    XDG_DATA_HOME: Path
    COMPLETIONS_PATH: Path
