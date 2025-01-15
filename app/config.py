"""Machine configuration files models."""

from abc import ABC
from pathlib import Path

import typer
from pydantic import BaseModel

from app import APP_NAME


class Machine(BaseModel, ABC):
    """Machine configuration files."""

    machine: Path = Path(__file__).parent.parent
    config: Path = machine / "config"
    data: Path = Path(typer.get_app_dir(APP_NAME))


class Private(Machine):
    """Private configuration files."""

    config: Path = Machine().config.parent / "private"
    private_env: Path = config / "private.sh"
    ssh_keys: Path = config / "keys"


class Default(Machine):
    """Default machine configuration files."""

    machine_id: str = "core"
    config: Path = Machine().config / machine_id

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
    config: Path = Machine().config / machine_id

    zshrc: Path = config / "zshrc"


class Gleason(Default):
    """Gleason configuration files."""

    machine_id: str = "gleason"
    config: Path = Machine().config / machine_id

    gitconfig: Path = config / ".gitconfig"


class MacOS(Private, Default):
    """macOS configuration files."""

    machine_id: str = "macos"
    config: Path = Machine().config / machine_id
    hostname: str = "mohds-macbook"

    brewfile: Path = config / "Brewfile"
    system_preferences: Path = config / "preferences.sh"
    ssh_config: Path = config / "ssh.config"
    zshenv: Path = config / "zshenv"
    zshrc: Path = config / "zshrc"
    ghostty: Path = config / "ghostty.config"

    gitconfig: Path = config / ".gitconfig"
    gitignore: Path = config / ".gitignore"


class RPi(Private, Default):
    """Raspberry Pi configuration files."""

    machine_id: str = "rpi"
    config: Path = Machine().config / machine_id

    ssh_config: Path = config / "ssh.config"
    zshenv: Path = config / "zshenv"
    zshrc: Path = config / "zshrc"


class Windows(Private, Default):
    """Windows configuration files."""

    machine_id: str = "windows"
    config: Path = Machine().config / machine_id

    ps_profile: Path = config / "ps_profile.ps1"
    ssh_config: Path = config / "ssh.config"
