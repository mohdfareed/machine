"""Machine configuration models."""

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel


class Machine(BaseModel):
    """config machine configuration files."""

    machine: ClassVar[Path] = Path(__file__).parent.parent
    config: ClassVar[Path] = machine / "config"


class Default(Machine):
    """Default machine configuration files."""

    config: ClassVar[Path] = Machine.config / "core"
    vim: ClassVar[Path] = config / "vim"
    vscode: ClassVar[Path] = config / "vscode"

    gitconfig: ClassVar[Path] = config / ".gitconfig"
    gitignore: ClassVar[Path] = config / ".gitignore"

    ps_profile: ClassVar[Path] = config / "ps_profile.ps1"
    zshenv: ClassVar[Path] = config / "zshenv"
    zshrc: ClassVar[Path] = config / "zshrc"

    tmux: ClassVar[Path] = config / "tmux.conf"
    zed_settings: ClassVar[Path] = config / "zed_settings.jsonc"


class Private(Machine):
    """Private configuration files."""

    config: ClassVar[Path] = Machine.config / "private"
    private_env: ClassVar[Path] = config / "private.sh"
    ssh_keys: ClassVar[Path] = config / "keys"


class Codespaces(Machine):
    """Github codespaces configuration files."""

    config: ClassVar[Path] = Machine.config / "codespaces"
    zshrc: ClassVar[Path] = config / "zshrc"


class Gleason(Machine):
    """Gleason configuration files."""

    config: ClassVar[Path] = Machine.config / "gleason"
    gitconfig: ClassVar[Path] = config / ".gitconfig"


class MacOS(Machine):
    """macOS configuration files."""

    config: ClassVar[Path] = Machine.config / "macos"
    brewfile: ClassVar[Path] = config / "Brewfile"
    system_preferences: ClassVar[Path] = config / "preferences.json"
    ssh_config: ClassVar[Path] = config / "ssh.config"
    zshenv: ClassVar[Path] = config / "zshenv"
    zshrc: ClassVar[Path] = config / "zshrc"


class RPi(Machine):
    """Raspberry Pi configuration files."""

    config: ClassVar[Path] = Machine.config / "rpi"
    ssh_config: ClassVar[Path] = config / "ssh.config"
    zshenv: ClassVar[Path] = config / "zshenv"
    zshrc: ClassVar[Path] = config / "zshrc"


class Windows(Machine):
    """Windows configuration files."""

    config: ClassVar[Path] = Machine.config / "windows"
    ps_profile: ClassVar[Path] = config / "ps_profile.ps1"
    ssh_config: ClassVar[Path] = config / "ssh.config"
