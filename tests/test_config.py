"""Machine configuration tests."""

from pathlib import Path

from pytest import MonkeyPatch

from app.config import (
    CodespacesConfig,
    GleasonConfig,
    MachineConfig,
    MacOSConfig,
    RPiConfig,
    UnixEnvironment,
    WindowsConfig,
    WindowsEnvironment,
)


def test_unix_env(monkeypatch: MonkeyPatch) -> None:
    """Test Unix environment variables."""

    monkeypatch.setenv("XDG_CONFIG_HOME", "config_home")
    monkeypatch.setenv("XDG_DATA_HOME", "data_home")
    monkeypatch.setenv("COMPLETIONS_PATH", "completions_path")
    unix_env = UnixEnvironment()

    assert unix_env.XDG_CONFIG_HOME == Path("config_home")
    assert unix_env.XDG_DATA_HOME == Path("data_home")
    assert unix_env.COMPLETIONS_PATH == Path("completions_path")


def test_unix_env_defaults(monkeypatch: MonkeyPatch) -> None:
    """Test Unix environment variables."""

    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("COMPLETIONS_PATH", raising=False)
    monkeypatch.delenv("COMPLETIONS_PATH", raising=False)
    unix_env = UnixEnvironment()

    assert unix_env.XDG_CONFIG_HOME == Path.home() / ".config"
    assert unix_env.XDG_DATA_HOME == Path.home() / ".local/share"
    assert unix_env.COMPLETIONS_PATH is None


def test_windows_env(monkeypatch: MonkeyPatch) -> None:
    """Test Windows environment variables."""

    monkeypatch.setenv("APPDATA", "appdata")
    monkeypatch.setenv("LOCALAPPDATA", "localappdata")
    windows_env = WindowsEnvironment()

    assert windows_env.APPDATA == Path("appdata")
    assert windows_env.LOCALAPPDATA == Path("localappdata")


def test_windows_env_defaults(monkeypatch: MonkeyPatch) -> None:
    """Test Windows environment variables."""

    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    windows_env = WindowsEnvironment()

    assert windows_env.APPDATA == Path.home() / "AppData" / "Roaming"
    assert windows_env.LOCALAPPDATA == Path.home() / "AppData" / "Local"


def test_config_files() -> None:
    """Test base MachineConfig configuration files."""

    config_files = MachineConfig()
    machine = Path(__file__).parent.parent
    config = machine / "config"
    config_path = config / "core"

    assert config_files.machine == machine
    assert config_files.config == config
    assert config_files.config_path == config_path

    assert config_files.vim == config_path / "vim"
    assert config_files.vscode == config_path / "vscode"

    assert config_files.gitconfig == config_path / ".gitconfig"
    assert config_files.gitignore == config_path / ".gitignore"

    assert config_files.ps_profile == config_path / "ps_profile.ps1"
    assert config_files.zshrc == config_path / "zshrc"
    assert config_files.zshenv == config_path / "zshenv"

    assert config_files.tmux == config_path / "tmux.conf"
    assert config_files.zed_settings == config_path / "zed_settings.jsonc"

    assert config_files.private_env == config_path / "private.env"
    assert config_files.ssh_keys == config_path / "keys"


def test_codespaces_config_files() -> None:
    """Test CodespacesConfig configuration files."""

    codespaces_config = CodespacesConfig()
    machine = Path(__file__).parent.parent
    config = machine / "config"
    config_path = config / "codespaces"

    assert codespaces_config.machine == machine
    assert codespaces_config.config == config
    assert codespaces_config.config_path == config_path
    assert codespaces_config.zshrc == config_path / "zshrc"


def test_gleason_config_files() -> None:
    """Test GleasonConfig configuration files."""

    gleason_config = GleasonConfig()
    machine = Path(__file__).parent.parent
    config = machine / "config"
    config_path = config / "gleason"

    assert gleason_config.machine == machine
    assert gleason_config.config == config
    assert gleason_config.config_path == config_path
    assert gleason_config.gitconfig == config_path / ".gitconfig"


def test_macos_config_files() -> None:
    """Test macOSConfig configuration files."""

    macos_config = MacOSConfig()
    machine = Path(__file__).parent.parent
    config = machine / "config"
    config_path = config / "macos"

    assert macos_config.machine == machine
    assert macos_config.config == config
    assert macos_config.config_path == config_path
    assert macos_config.brewfile == config_path / "Brewfile"
    assert macos_config.system_preferences == config_path / "preferences.json"
    assert macos_config.ssh_config == config_path / "ssh.config"
    assert macos_config.zshenv == config_path / "zshenv"
    assert macos_config.zshrc == config_path / "zshrc"


def test_rpi_config_files() -> None:
    """Test RPiConfig configuration files."""

    rpi_config = RPiConfig()
    machine = Path(__file__).parent.parent
    config = machine / "config"
    config_path = config / "rpi"

    assert rpi_config.machine == machine
    assert rpi_config.config == config
    assert rpi_config.config_path == config_path
    assert rpi_config.ssh_config == config_path / "ssh.config"
    assert rpi_config.zshenv == config_path / "zshenv"
    assert rpi_config.zshrc == config_path / "zshrc"


def test_windows_config_files() -> None:
    """Test WindowsConfig configuration files."""

    windows_config = WindowsConfig()
    machine = Path(__file__).parent.parent
    config = machine / "config"
    config_path = config / "windows"

    assert windows_config.machine == machine
    assert windows_config.config == config
    assert windows_config.config_path == config_path
    assert windows_config.ps_profile == config_path / "ps_profile.ps1"
    assert windows_config.ssh_config == config_path / "ssh.config"
