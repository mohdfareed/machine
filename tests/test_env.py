"""Machine configuration tests."""

from pathlib import Path

import pytest
from pytest import MonkeyPatch

from app import env, utils


def test_env_fail() -> None:
    """Test the environment variables failing."""
    with pytest.raises(utils.ShellError):
        env.Default().load(Path("."))


def test_unix_env(monkeypatch: MonkeyPatch) -> None:
    """Test Unix environment variables."""

    monkeypatch.setenv("XDG_CONFIG_HOME", "config_home")
    unix_env = env.Unix()
    assert unix_env.XDG_CONFIG_HOME == Path("config_home")


def test_unix_env_defaults(monkeypatch: MonkeyPatch) -> None:
    """Test Unix environment variables."""

    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("COMPLETIONS_PATH", raising=False)
    unix_env = env.Unix()

    assert unix_env.XDG_CONFIG_HOME == Path.home() / ".config"
    assert unix_env.COMPLETIONS_PATH is None


def test_windows_env(monkeypatch: MonkeyPatch) -> None:
    """Test Windows environment variables."""

    monkeypatch.setenv("USERPROFILE", "userprofile")
    windows_env = env.Windows()
    assert windows_env.USERPROFILE == Path("userprofile")


def test_windows_env_defaults(monkeypatch: MonkeyPatch) -> None:
    """Test Windows environment variables."""

    monkeypatch.delenv("USERPROFILE", raising=False)
    windows_env = env.Windows()
    assert windows_env.USERPROFILE == Path.home()


def test_unix_loaded_env(monkeypatch: MonkeyPatch) -> None:
    """Test Unix environment variables."""

    monkeypatch.setattr(utils, "WINDOWS", False)
    monkeypatch.setenv("MACHINE", "test")
    unix_env = env.Unix().load()
    assert unix_env.MACHINE != Path("test")


def test_windows_loaded_env(monkeypatch: MonkeyPatch) -> None:
    """Test Windows environment variables."""

    monkeypatch.setattr(utils, "WINDOWS", True)
    monkeypatch.setenv("MACHINE", "test")
    windows_env = env.Windows().load()
    assert windows_env.MACHINE != Path("test")
