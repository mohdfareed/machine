"""Environment variables models."""

from pathlib import Path

import platformdirs

from app import plugins
from app.models import Environment


class Machine(plugins.SSHEnv, Environment):
    """Default machine environment variables."""

    SSH_DIR: Path = Path.home() / ".ssh"


class Unix(
    plugins.PythonEnv,
    plugins.GitEnv,
    plugins.ShellEnv,
    plugins.VSCodeEnv,
    plugins.PowerShellEnv,
    plugins.NeoVimEnv,
    Machine,
):
    """Unix environment variables."""

    XDG_CONFIG_HOME: Path = platformdirs.user_config_path()
    XDG_DATA_HOME: Path = platformdirs.user_data_path()
    COMPLETIONS_PATH: Path = XDG_DATA_HOME / "zinit" / "completions"
    ZDOTDIR: Path = XDG_CONFIG_HOME / "zsh"

    GITCONFIG: Path = XDG_CONFIG_HOME / "git" / "config"
    GITIGNORE: Path = XDG_CONFIG_HOME / "git" / "ignore"
    VSCODE: Path = platformdirs.user_config_path() / "Code" / "User"

    VIM: Path = XDG_CONFIG_HOME / "nvim"
    TMUX_CONFIG: Path = XDG_CONFIG_HOME / "tmux" / "tmux.conf"
    PS_PROFILE: Path = XDG_CONFIG_HOME / "powershell" / "profile.ps1"
    ZSHRC: Path = ZDOTDIR / ".zshrc"
    ZSHENV: Path = Path.home() / ".zshenv"
    ZED_SETTINGS: Path = XDG_CONFIG_HOME / "zed" / "settings.json"


class Windows(plugins.GitEnv, Machine):
    """Windows environment variables."""

    USERPROFILE: Path = Path.home()
    APPDATA: Path = platformdirs.user_data_path(roaming=True)
    LOCALAPPDATA: Path = platformdirs.user_data_path()

    GITCONFIG: Path = USERPROFILE / ".gitconfig"
    GITIGNORE: Path = USERPROFILE / ".gitignore"
    VIM: Path = LOCALAPPDATA / "nvim"
    PS_PROFILE: Path = USERPROFILE / "Documents" / "WindowsPowerShell" / "profile.ps1"
    VSCODE: Path = APPDATA / "Code" / "User"


class MacOS(Unix):
    """MacOS environment variables."""

    ICLOUD: Path = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
