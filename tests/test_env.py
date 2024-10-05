"""Machine configuration tests."""

from pathlib import Path

from pytest import MonkeyPatch

from app import env


def test_unix_env(monkeypatch: MonkeyPatch) -> None:
    """Test Unix environment variables."""

    monkeypatch.setenv("XDG_CONFIG_HOME", "config_home")
    monkeypatch.setenv("XDG_DATA_HOME", "data_home")
    monkeypatch.setenv("COMPLETIONS_PATH", "completions_path")
    unix_env = env.Unix()

    assert unix_env.XDG_CONFIG_HOME == Path("config_home")
    assert unix_env.XDG_DATA_HOME == Path("data_home")
    assert unix_env.COMPLETIONS_PATH == Path("completions_path")


def test_unix_env_defaults(monkeypatch: MonkeyPatch) -> None:
    """Test Unix environment variables."""

    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("COMPLETIONS_PATH", raising=False)
    monkeypatch.delenv("COMPLETIONS_PATH", raising=False)
    unix_env = env.Unix()

    assert unix_env.XDG_CONFIG_HOME == Path.home() / ".config"
    assert unix_env.XDG_DATA_HOME == Path.home() / ".local/share"
    assert unix_env.COMPLETIONS_PATH is None


def test_windows_env(monkeypatch: MonkeyPatch) -> None:
    """Test Windows environment variables."""

    monkeypatch.setenv("APPDATA", "appdata")
    monkeypatch.setenv("LOCALAPPDATA", "localappdata")
    windows_env = env.Windows()

    assert windows_env.APPDATA == Path("appdata")
    assert windows_env.LOCALAPPDATA == Path("localappdata")


def test_windows_env_defaults(monkeypatch: MonkeyPatch) -> None:
    """Test Windows environment variables."""

    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    windows_env = env.Windows()

    assert windows_env.APPDATA == Path.home() / "AppData" / "Roaming"
    assert windows_env.LOCALAPPDATA == Path.home() / "AppData" / "Local"
