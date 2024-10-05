"""Environment variables models."""

import getpass
from abc import ABC
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(BaseSettings, ABC):
    """Environment variables."""

    model_config = SettingsConfigDict()


class Unix(Environment):
    """Unix environment variables."""

    XDG_CONFIG_HOME: Path = Path.home() / ".config"
    XDG_DATA_HOME: Path = Path.home() / ".local/share"
    COMPLETIONS_PATH: Optional[Path] = None


class Windows(Environment):
    """Windows environment variables."""

    APPDATA: Path = Path.home() / "AppData" / "Roaming"
    LOCALAPPDATA: Path = Path.home() / "AppData" / "Local"
    USERPROFILE: Path = Path.home() / "User" / getpass.getuser()
