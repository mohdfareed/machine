"""Machine configuration models."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigFiles(BaseModel):
    """Machine configuration files."""

    machine: Path = Path(__file__).parent.parent
    config_path: Path = machine / "config"

    vim: Path = config_path / "vim"
    vscode: Path = config_path / "vscode"

    gitconfig: Path = config_path / ".gitconfig"
    gitignore: Path = config_path / ".gitignore"

    ps_profile: Path = config_path / "ps_profile.ps1"
    zshrc: Path = config_path / "zshrc"
    zshenv: Path = config_path / "zshenv"

    tmux: Path = config_path / "tmux.conf"
    zed_settings: Path = config_path / "zed_settings.jsonc"

    private_env: Path = config_path / "private.env"
    ssh_keys: Path = config_path / "keys"


class UnixEnvironment(BaseSettings):
    """Unix environment variables."""

    XDG_CONFIG_HOME: Path = Path.home() / ".config"
    XDG_DATA_HOME: Path = Path.home() / ".local/share"
    COMPLETIONS_PATH: Optional[Path] = None

    model_config = SettingsConfigDict()


class WindowsEnvironment(BaseSettings):
    """Windows environment variables."""

    APPDATA: Path = Path.home() / "AppData" / "Roaming"
    LOCALAPPDATA: Path = Path.home() / "AppData" / "Local"

    model_config = SettingsConfigDict()
