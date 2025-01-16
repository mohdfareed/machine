"""Machine configuration files models."""

__all__ = [
    "MachineConfig",
    "Private",
    "Default",
    "Codespaces",
    "Gleason",
    "MacOS",
    "RPi",
    "Windows",
]

from abc import ABC
from pathlib import Path

import typer
from pydantic import BaseModel

from app import APP_NAME


class MachineConfig(BaseModel, ABC):
    """Machine configuration files."""

    machine: Path = Path(__file__).parent.parent
    config: Path = machine / "config"
    data: Path = Path(typer.get_app_dir(APP_NAME))


class Private(MachineConfig):
    """Private configuration files."""

    config: Path = MachineConfig().config.parent / "private"
    private_env: Path = config / "private.sh"
    ssh_keys: Path = config / "keys"


class Default(MachineConfig):
    """Default machine configuration files."""

    machine_id: str = "core"
    config: Path = MachineConfig().config / machine_id

    vim: Path = config / "vim"
    vscode: Path = config / "vscode"

    gitconfig: Path = config / ".gitconfig"
    gitignore: Path = config / ".gitignore"

    ps_profile: Path = config / "ps_profile.ps1"
    zshenv: Path = config / "zshenv"
    zshrc: Path = config / "zshrc"

    tmux_config: Path = config / "tmux.conf"
    zed_settings: Path = config / "zed_settings.jsonc"


class Codespaces(Default):
    """Github codespaces configuration files."""

    machine_id: str = "codespaces"
    config: Path = MachineConfig().config / machine_id
    zshrc: Path = config / "zshrc"


class Gleason(Default):
    """Gleason configuration files."""

    machine_id: str = "gleason"
    config: Path = MachineConfig().config / machine_id
    gitconfig: Path = config / ".gitconfig"


class MacOS(Private, Default):
    """macOS configuration files."""

    machine_id: str = "macos"
    config: Path = MachineConfig().config / machine_id
    hostname: str = "mohds-macbook"

    zshenv: Path = config / "zshenv"
    zshrc: Path = config / "zshrc"
    ghostty: Path = config / "ghostty.config"

    gitconfig: Path = config / ".gitconfig"
    gitignore: Path = config / ".gitignore"
    ssh_config: Path = config / "ssh.config"
    brewfile: Path = config / "Brewfile"
    system_preferences: Path = config / "preferences.sh"


class RPi(Private, Default):
    """Raspberry Pi configuration files."""

    machine_id: str = "rpi"
    config: Path = MachineConfig().config / machine_id

    ssh_config: Path = config / "ssh.config"
    zshenv: Path = config / "zshenv"
    zshrc: Path = config / "zshrc"


class Windows(Private, Default):
    """Windows configuration files."""

    machine_id: str = "windows"
    config: Path = MachineConfig().config / machine_id
    ps_profile: Path = config / "ps_profile.ps1"
    ssh_config: Path = config / "ssh.config"
