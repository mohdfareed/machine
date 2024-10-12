"""Machine configuration tests."""

from pathlib import Path

from app.config import Codespaces, Default, Gleason, Machine, MacOS, RPi, Windows


def test_machine_config() -> None:
    """Test MachineConfig configuration files."""

    machine_config = Machine()
    machine = Path(__file__).parent.parent
    assert machine_config.machine == machine


def test_config_files() -> None:
    """Test base MachineConfig configuration files."""

    config_files = Default()
    config = Path(__file__).parent.parent / "config" / "core"
    assert config_files.config == config


def test_codespaces_config_files() -> None:
    """Test CodespacesConfig configuration files."""

    codespaces_config = Codespaces()
    config = Path(__file__).parent.parent / "config" / "codespaces"
    assert codespaces_config.zshrc == config / "zshrc"


def test_gleason_config_files() -> None:
    """Test GleasonConfig configuration files."""

    gleason_config = Gleason()
    config = Path(__file__).parent.parent / "config" / "gleason"
    assert gleason_config.config == config


def test_macos_config_files() -> None:
    """Test macOSConfig configuration files."""

    macos_config = MacOS()
    config = Path(__file__).parent.parent / "config" / "macos"
    assert macos_config.config == config


def test_rpi_config_files() -> None:
    """Test RPiConfig configuration files."""

    rpi_config = RPi()
    config = Path(__file__).parent.parent / "config" / "rpi"
    assert rpi_config.config == config


def test_windows_config_files() -> None:
    """Test WindowsConfig configuration files."""

    windows_config = Windows()
    config = Path(__file__).parent.parent / "config" / "windows"
    assert windows_config.config == config
