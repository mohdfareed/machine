"""Machine configuration models."""

from pathlib import Path

from pydantic import BaseModel


class Machine(BaseModel):
    """config machine configuration files."""

    machine: Path = Path(__file__).parent.parent
    config: Path = machine / "config"


class Default(Machine):
    """Default machine configuration files."""

    config: Path = Machine().config / "core"
    vim: Path = config / "vim"
    vscode: Path = config / "vscode"

    gitconfig: Path = config / ".gitconfig"
    gitignore: Path = config / ".gitignore"

    ps_profile: Path = config / "ps_profile.ps1"
    zshenv: Path = config / "zshenv"
    zshrc: Path = config / "zshrc"

    tmux: Path = config / "tmux.conf"
    zed_settings: Path = config / "zed_settings.jsonc"


class Private(Machine):
    """Private configuration files."""

    config: Path = Machine().config / "private"
    private_env: Path = config / "private.sh"
    ssh_keys: Path = config / "keys"


class Codespaces(Machine):
    """Github codespaces configuration files."""

    config: Path = Machine().config / "codespaces"
    zshrc: Path = config / "zshrc"


class Gleason(Machine):
    """Gleason configuration files."""

    config: Path = Machine().config / "gleason"
    gitconfig: Path = config / ".gitconfig"


class MacOS(Machine):
    """macOS configuration files."""

    config: Path = Machine().config / "macos"
    brewfile: Path = config / "Brewfile"
    system_preferences: Path = config / "preferences.json"
    ssh_config: Path = config / "ssh.config"
    zshenv: Path = config / "zshenv"
    zshrc: Path = config / "zshrc"


class RPi(Machine):
    """Raspberry Pi configuration files."""

    config: Path = Machine().config / "rpi"
    ssh_config: Path = config / "ssh.config"
    zshenv: Path = config / "zshenv"
    zshrc: Path = config / "zshrc"


class Windows(Machine):
    """Windows configuration files."""

    config: Path = Machine().config / "windows"
    ps_profile: Path = config / "ps_profile.ps1"
    ssh_config: Path = config / "ssh.config"
