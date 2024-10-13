"""Environment variables models."""

from pathlib import Path
from typing import Annotated, Optional

from app import config, utils
from app.models import BaseEnvironment, T


class Environment(BaseEnvironment):
    """Machine environment variables."""

    MACHINE: Path = Path(__file__).parent.parent
    GITCONFIG: Path = Path.home() / ".gitconfig"
    GITIGNORE: Path = Path.home() / ".gitignore"
    SSH_DIR: Path = Path.home() / ".ssh"
    VSCODE: Path = Path.home() / ".config" / "Code" / "User"

    def load(self: T, env: Optional[Path] = None) -> T:
        env = env or (
            config.Default().ps_profile if utils.WINDOWS else config.Default().zshenv
        )
        env_vars = utils.load_env(env)

        utils.LOGGER.debug("Loading environment from: %s", env)
        for field in self.model_fields:
            if field in env_vars:
                setattr(self, field, env_vars[field])
        return self


class Unix(Environment):
    """Unix environment variables."""

    XDG_CONFIG_HOME: Path = Path.home() / ".config"
    XDG_DATA_HOME: Path = Path.home() / ".local/share"
    COMPLETIONS_PATH: Optional[Path] = None
    ZDOTDIR: Path = XDG_CONFIG_HOME / "zsh"

    GITCONFIG: Path = XDG_CONFIG_HOME / "git" / "config"
    GITIGNORE: Path = XDG_CONFIG_HOME / "git" / "ignore"
    VIM: Path = XDG_CONFIG_HOME / "nvim"
    TMUX_CONFIG: Path = XDG_CONFIG_HOME / "tmux" / "tmux.conf"
    PS_PROFILE: Path = XDG_CONFIG_HOME / "powershell" / "profile.ps1"
    ZSHRC: Path = ZDOTDIR / ".zshrc"
    ZSHENV: Path = Path.home() / ".zshenv"
    VSCODE: Path = (
        Environment().VSCODE
        if not utils.MACOS
        else (Path.home() / "Library" / "Application Support" / "Code" / "User")
    )
    ZED_SETTINGS: Path = XDG_CONFIG_HOME / "zed" / "settings.json"


class Windows(Environment):
    """Windows environment variables."""

    USERPROFILE: Path = Path.home()
    APPDATA: Path = Path.home() / "AppData" / "Roaming"
    LOCALAPPDATA: Path = Path.home() / "AppData" / "Local"

    GITCONFIG: Path = USERPROFILE / ".gitconfig"
    GITIGNORE: Path = USERPROFILE / ".gitignore"
    VIM: Path = LOCALAPPDATA / "nvim"
    PS_PROFILE: Path = USERPROFILE / "Documents" / "WindowsPowerShell" / "profile.ps1"
    VSCODE: Path = APPDATA / "Code" / "User"


Default = Windows if utils.WINDOWS else Unix
EnvArg = Annotated[Environment, utils.InternalArg]
WinEnvArg = Annotated[Windows, utils.InternalArg]
UnixEnvArg = Annotated[Unix, utils.InternalArg]
