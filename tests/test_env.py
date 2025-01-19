"""Machine configuration tests."""

from pathlib import Path

import pytest
from pytest import MonkeyPatch

from app import env, utils


def test_env_fail() -> None:
    """Test the environment variables failing."""
    with pytest.raises(IsADirectoryError):
        env.MachineEnv(env_file=Path("."))


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

    if utils.Platform.MACOS:
        assert (
            unix_env.XDG_CONFIG_HOME == Path.home() / "Library" / "Application Support"
        )
    else:
        assert unix_env.XDG_CONFIG_HOME == Path.home() / ".config"
    assert unix_env.SSH_DIR == Path.home() / ".ssh"


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

    temp_file = utils.create_temp_file()
    temp_file.write_text(
        """
        export GITCONFIG="./test"
        """.strip()
    )

    monkeypatch.setattr(utils, "WINDOWS", False)
    unix_env = env.Unix(env_file=temp_file)
    assert Path(unix_env.GITCONFIG) == Path("test")


def test_windows_loaded_env(monkeypatch: MonkeyPatch) -> None:
    """Test Windows environment variables."""

    temp_file = utils.create_temp_file(".ps1")
    temp_file.write_text(
        """
        $env:GITCONFIG="./test"
        """.strip()
    )

    monkeypatch.setattr(utils, "WINDOWS", True)
    windows_env = env.Windows(env_file=temp_file)
    assert Path(windows_env.GITCONFIG) == Path("test")
