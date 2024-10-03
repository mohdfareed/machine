"""Machine configuration tests."""

from pathlib import Path

from pytest import MonkeyPatch

from app.config import ConfigFiles, UnixEnvironment, WindowsEnvironment


def test_config_files():
    """Test configuration files."""

    config_files = ConfigFiles()
    machine = Path(__file__).parent.parent
    config_path = machine / "config"

    assert config_files.machine == machine
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


def test_unix_env(monkeypatch: MonkeyPatch):
    """Test Unix environment variables."""

    monkeypatch.setenv("XDG_CONFIG_HOME", "config_home")
    monkeypatch.setenv("XDG_DATA_HOME", "data_home")
    monkeypatch.setenv("COMPLETIONS_PATH", "completions_path")
    unix_env = UnixEnvironment()

    assert unix_env.XDG_CONFIG_HOME == Path("config_home")
    assert unix_env.XDG_DATA_HOME == Path("data_home")
    assert unix_env.COMPLETIONS_PATH == Path("completions_path")


def test_unix_env_defaults(monkeypatch: MonkeyPatch):
    """Test Unix environment variables."""

    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("COMPLETIONS_PATH", raising=False)
    monkeypatch.delenv("COMPLETIONS_PATH", raising=False)
    unix_env = UnixEnvironment()

    assert unix_env.XDG_CONFIG_HOME == Path.home() / ".config"
    assert unix_env.XDG_DATA_HOME == Path.home() / ".local/share"
    assert unix_env.COMPLETIONS_PATH is None


def test_windows_env(monkeypatch: MonkeyPatch):
    """Test Windows environment variables."""

    monkeypatch.setenv("APPDATA", "appdata")
    monkeypatch.setenv("LOCALAPPDATA", "localappdata")
    windows_env = WindowsEnvironment()

    assert windows_env.APPDATA == Path("appdata")
    assert windows_env.LOCALAPPDATA == Path("localappdata")


def test_windows_env_defaults(monkeypatch: MonkeyPatch):
    """Test Windows environment variables."""

    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    windows_env = WindowsEnvironment()

    assert windows_env.APPDATA == Path.home() / "AppData" / "Roaming"
    assert windows_env.LOCALAPPDATA == Path.home() / "AppData" / "Local"
