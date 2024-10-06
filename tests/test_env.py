"""Machine configuration tests."""

from pathlib import Path

import pytest
from pytest import MonkeyPatch

from app import env
from app.config import Default


def test_env_fail() -> None:
    """Test the environment variables failing."""
    with pytest.raises(RuntimeError):
        env.Environment.os_env().load(Path("."))


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

    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
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

    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    windows_env = env.Windows()

    assert windows_env.APPDATA == Path.home() / "AppData" / "Roaming"
    assert windows_env.LOCALAPPDATA == Path.home() / "AppData" / "Local"


def test_unix_loaded_env(monkeypatch: MonkeyPatch) -> None:
    """Test Unix environment variables."""

    monkeypatch.setenv("MACHINE", "test")
    unix_env = env.Unix.load()
    assert unix_env.MACHINE != Path("test")


def test_windows_loaded_env(monkeypatch: MonkeyPatch) -> None:
    """Test Windows environment variables."""

    monkeypatch.setenv("MACHINE", "test")
    windows_env = env.Windows.load(Default().ps_profile)
    assert windows_env.MACHINE != Path("test")
