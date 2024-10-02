"""Machine configuration tests."""

import os
from pathlib import Path

import pytest

from app.config import ConfigFiles
from app.env import Machine, Unix, Windows, load_var_var

_is_windows = os.name == "nt"


def test_environment():
    """Test environment variables."""

    environment = Machine()
    assert environment.MACHINE == Path(
        os.getenv("MACHINE") or str(Path.home() / ".machine")
    )

    private_env = os.getenv("PRIVATE_ENV")
    assert environment.PRIVATE_ENV == Path(private_env) if private_env else None
    ssh_keys = os.getenv("SSH_KEYS")
    assert environment.SSH_KEYS == Path(ssh_keys) if ssh_keys else None


def test_windows_variables():
    """Test Windows environment variables."""
    if not _is_windows:
        return

    windows_variables = Windows()
    assert windows_variables.LOCALAPPDATA == Path(os.environ["LOCALAPPDATA"])
    assert windows_variables.APPDATA == Path(os.environ["APPDATA"])


def test_unix_variables():
    """Test Unix environment variables."""
    if _is_windows:
        return

    unix_variables = Unix()

    config_home = os.getenv("XDG_CONFIG_HOME")
    assert unix_variables.XDG_CONFIG_HOME == Path(
        config_home or str(Path.home() / ".config")
    )
    data_home = os.getenv("XDG_DATA_HOME")
    assert unix_variables.XDG_DATA_HOME == Path(
        data_home or str(Path.home() / ".local" / "share")
    )
    comps = os.getenv("COMPLETIONS_PATH")
    assert unix_variables.COMPLETIONS_PATH == Path(comps) if comps else None


def test_env_load():
    """Test environment loading."""
    config = ConfigFiles()
    machine = load_var_var("MACHINE", config.zshenv, "bash")
    assert machine == str(config.zshenv.parent.parent)


def test_env_file_fail():
    """Test environment file loading failure."""

    machine = Machine()
    with pytest.raises(FileNotFoundError):
        machine.load(Path("nonexistent"), "bash")


def test_env_file():
    """Test environment file loading."""
    config = ConfigFiles()
    env_file = config.zshenv

    machine = Machine()
    machine.load(env_file, "bash")
    assert machine.MACHINE == config.zshenv.parent.parent
    assert machine.PRIVATE_ENV == machine.MACHINE / "config" / "private.sh"
    assert machine.SSH_KEYS == machine.MACHINE / "config" / "keys"

    unix = Unix()
    unix.load(env_file, "bash")
    assert unix.XDG_CONFIG_HOME == Path.home() / ".config"
    assert unix.XDG_DATA_HOME == Path.home() / ".local" / "share"
    assert unix.COMPLETIONS_PATH == unix.XDG_DATA_HOME / "zinit" / "completions"

    if _is_windows:
        windows = Windows()
        windows.load(env_file, "bash")
        assert windows.LOCALAPPDATA == Path(os.environ["LOCALAPPDATA"])
        assert windows.APPDATA == Path(os.environ["APPDATA"])


def test_pwsh_unix():
    """Test PowerShell Unix environment variables."""
    config = ConfigFiles()
    env_file = config.ps_profile

    machine = Machine()
    machine.load(env_file, "pwsh")
    assert machine.MACHINE == config.zshenv.parent.parent
    assert machine.PRIVATE_ENV == machine.MACHINE / "config" / "private.ps1"
    assert machine.SSH_KEYS == machine.MACHINE / "config" / "keys"

    unix = Unix()
    unix.load(env_file, "pwsh")
    assert unix.XDG_CONFIG_HOME == Path.home() / ".config"
    assert unix.XDG_DATA_HOME == Path.home() / ".local" / "share"
    assert unix.COMPLETIONS_PATH == unix.XDG_DATA_HOME / "zinit" / "completions"
