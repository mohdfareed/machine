"""Machine configuration models."""

from abc import ABC
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(BaseSettings, ABC):
    """Environment variables."""

    model_config = SettingsConfigDict()


class UnixEnvironment(Environment):
    """Unix environment variables."""

    XDG_CONFIG_HOME: Path = Path.home() / ".config"
    XDG_DATA_HOME: Path = Path.home() / ".local/share"
    COMPLETIONS_PATH: Optional[Path] = None


class WindowsEnvironment(Environment):
    """Windows environment variables."""

    APPDATA: Path = Path.home() / "AppData" / "Roaming"
    LOCALAPPDATA: Path = Path.home() / "AppData" / "Local"


class MachineConfig(BaseModel):
    """Core machine configuration files."""

    machine: Path = Path(__file__).parent.parent
    config: Path = machine / "config"

    config_path: Path = config / "core"
    vim: Path = config_path / "vim"
    vscode: Path = config_path / "vscode"

    gitconfig: Path = config_path / ".gitconfig"
    gitignore: Path = config_path / ".gitignore"

    ps_profile: Path = config_path / "ps_profile.ps1"
    zshenv: Path = config_path / "zshenv"
    zshrc: Path = config_path / "zshrc"

    tmux: Path = config_path / "tmux.conf"
    zed_settings: Path = config_path / "zed_settings.jsonc"

    private_env: Path = config_path / "private.sh"
    ssh_keys: Path = config_path / "keys"


class CodespacesConfig(MachineConfig):
    """Github codespaces configuration files."""

    config_path: Path = MachineConfig().config / "codespaces"
    zshrc: Path = config_path / "zshrc"


class GleasonConfig(MachineConfig):
    """Gleason configuration files."""

    config_path: Path = MachineConfig().config / "gleason"
    gitconfig: Path = config_path / ".gitconfig"


class MacOSConfig(MachineConfig):
    """macOS configuration files."""

    config_path: Path = MachineConfig().config / "macos"
    brewfile: Path = config_path / "Brewfile"
    system_preferences: Path = config_path / "preferences.json"
    ssh_config: Path = config_path / "ssh.config"
    zshenv: Path = config_path / "zshenv"
    zshrc: Path = config_path / "zshrc"


class RPiConfig(MachineConfig):
    """Raspberry Pi configuration files."""

    config_path: Path = MachineConfig().config / "rpi"
    ssh_config: Path = config_path / "ssh.config"
    zshenv: Path = config_path / "zshenv"
    zshrc: Path = config_path / "zshrc"


class WindowsConfig(MachineConfig):
    """Windows configuration files."""

    config_path: Path = MachineConfig().config / "windows"
    ps_profile: Path = config_path / "ps_profile.ps1"
    ssh_config: Path = config_path / "ssh.config"
