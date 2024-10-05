"""Environment variables models."""

import getpass
from abc import ABC
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(BaseSettings, ABC):
    """Environment variables."""

    model_config = SettingsConfigDict()

    GITCONFIG: Path = Path.home() / ".gitconfig"
    GITIGNORE: Path = Path.home() / ".gitignore"


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
