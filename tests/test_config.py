"""Machine configuration tests."""

from pathlib import Path

from app.config import (
    Codespaces,
    Default,
    Gleason,
    Machine,
    MacOS,
    Private,
    RPi,
    Windows,
)


def test_machine_config() -> None:
    """Test MachineConfig configuration files."""

    machine_config = Machine
    machine = Path(__file__).parent.parent
    config = machine / "config"

    assert machine_config.machine == machine
    assert machine_config.config == config


def test_private_config() -> None:
    """Test PrivateConfig configuration files."""

    private_config = Private
    machine = Path(__file__).parent.parent
    config = machine / "config" / "private"

    assert private_config.config == config
    assert private_config.private_env == config / "private.sh"
    assert private_config.ssh_keys == config / "keys"


def test_config_files() -> None:
    """Test base MachineConfig configuration files."""

    config_files = Default
    machine = Path(__file__).parent.parent
    config = machine / "config" / "core"

    assert config_files.config == config
    assert config_files.vim == config / "vim"
    assert config_files.vscode == config / "vscode"

    assert config_files.gitconfig == config / ".gitconfig"
    assert config_files.gitignore == config / ".gitignore"

    assert config_files.ps_profile == config / "ps_profile.ps1"
    assert config_files.zshrc == config / "zshrc"
    assert config_files.zshenv == config / "zshenv"

    assert config_files.tmux == config / "tmux.conf"
    assert config_files.zed_settings == config / "zed_settings.jsonc"


def test_codespaces_config_files() -> None:
    """Test CodespacesConfig configuration files."""

    codespaces_config = Codespaces
    machine = Path(__file__).parent.parent
    config = machine / "config" / "codespaces"

    assert codespaces_config.config == config
    assert codespaces_config.zshrc == config / "zshrc"


def test_gleason_config_files() -> None:
    """Test GleasonConfig configuration files."""

    gleason_config = Gleason
    machine = Path(__file__).parent.parent
    config = machine / "config" / "gleason"

    assert gleason_config.config == config
    assert gleason_config.gitconfig == config / ".gitconfig"


def test_macos_config_files() -> None:
    """Test macOSConfig configuration files."""

    macos_config = MacOS
    machine = Path(__file__).parent.parent
    config = machine / "config" / "macos"

    assert macos_config.config == config
    assert macos_config.brewfile == config / "Brewfile"
    assert macos_config.system_preferences == config / "preferences.json"
    assert macos_config.ssh_config == config / "ssh.config"
    assert macos_config.zshenv == config / "zshenv"
    assert macos_config.zshrc == config / "zshrc"


def test_rpi_config_files() -> None:
    """Test RPiConfig configuration files."""

    rpi_config = RPi
    machine = Path(__file__).parent.parent
    config = machine / "config" / "rpi"

    assert rpi_config.config == config
    assert rpi_config.ssh_config == config / "ssh.config"
    assert rpi_config.zshenv == config / "zshenv"
    assert rpi_config.zshrc == config / "zshrc"


def test_windows_config_files() -> None:
    """Test WindowsConfig configuration files."""

    windows_config = Windows
    machine = Path(__file__).parent.parent
    config = machine / "config" / "windows"

    assert windows_config.machine == machine
    assert windows_config.config == config
    assert windows_config.ps_profile == config / "ps_profile.ps1"
    assert windows_config.ssh_config == config / "ssh.config"
