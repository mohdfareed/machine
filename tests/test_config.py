"""Machine configuration tests."""

import os
from pathlib import Path

from app.config import ConfigFiles, Environment, UnixVariables, WindowsVariables

_is_windows = os.name == "nt"


def test_config_files():
    """Test configuration files."""

    config_files = ConfigFiles()
    config_path = Path(__file__).parent.parent / "config"

    assert config_files.vim == config_path / "vim"
    assert config_files.vscode == config_path / "vscode"
    assert config_files.gitconfig == config_path / ".gitconfig"
    assert config_files.gitignore == config_path / ".gitignore"
    assert config_files.ps_profile == config_path / "ps_profile.ps1"
    assert config_files.tmux == config_path / "tmux.conf"
    assert config_files.zed_settings == config_path / "zed_settings.jsonc"
    assert config_files.zshrc == config_path / "zshrc"
    assert config_files.zshenv == config_path / "zshenv"


def test_environment():
    """Test environment variables."""
    environment = Environment(MACHINE=Path(), PRIVATE_ENV=Path(), SSH_KEYS=Path())

    assert environment.MACHINE == Path()
    assert environment.PRIVATE_ENV == Path()
    assert environment.SSH_KEYS == Path()


def test_windows_variables():
    """Test Windows environment variables."""
    if not _is_windows:
        return

    windows_variables = WindowsVariables()
    assert windows_variables.LOCALAPPDATA == Path(os.environ["LOCALAPPDATA"])
    assert windows_variables.APPDATA == Path(os.environ["APPDATA"])


def test_unix_variables():
    """Test Unix environment variables."""
    if _is_windows:
        return

    unix_variables = UnixVariables(
        COMPLETIONS_PATH=Path(),
        XDG_DATA_HOME=Path(),
        XDG_CONFIG_HOME=Path(),
    )

    assert unix_variables.XDG_CONFIG_HOME == Path()
    assert unix_variables.XDG_DATA_HOME == Path()
    assert unix_variables.COMPLETIONS_PATH == Path()
