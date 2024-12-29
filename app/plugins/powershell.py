"""PowerShell setup module."""

from pathlib import Path

from app import utils
from app.plugins.pkg_managers import Brew, SnapStore, Winget
from app.plugins.plugin import Configuration, Environment, Plugin, SetupFunc


class PowerShellConfig(Configuration):
    """PowerShell configuration files."""

    ps_profile: Path


class PowerShellEnv(Environment):
    """PowerShell environment variables."""

    PS_PROFILE: Path


class PowerShell(Plugin[PowerShellConfig, PowerShellEnv]):
    """Install PowerShell on a machine."""

    @property
    def plugin_setup(self) -> SetupFunc:
        return self._setup

    def _setup(self) -> None:
        if Brew().is_supported():
            Brew().install("powershell", cask=True)
        elif Winget().is_supported():
            Winget().install("Microsoft.PowerShell")
        elif SnapStore().is_supported():
            SnapStore().install("powershell")
        utils.link(self.config.ps_profile, self.env.PS_PROFILE)
