"""Machine configuration models."""

from abc import ABC
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings, ABC):
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
