"""PowerShell setup module."""

from pathlib import Path

from app import models, utils
from app.plugins.pkg_managers import Brew, SnapStore, Winget
from app.plugins.plugin import Plugin, SetupFunc

PS_PROFILE_TEMPLATE = """
$env:MACHINE="{{machine}}"
$env:MACHINE_ID={{machine_id}}
. {{machine_ps_profile}}
"""


class PowerShellConfig(models.ConfigFiles):
    """PowerShell configuration files."""

    machine_id: str
    machine: Path

    ps_profile: Path


class PowerShellEnv(models.Environment):
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

        # create machine identifier
        ps_profile_content = PS_PROFILE_TEMPLATE.format(
            machine=self.config.machine,
            machine_id=self.config.machine_id,
            machine_zshenv=self.config.ps_profile,
        )
        self.env.PS_PROFILE.write_text(ps_profile_content)

        utils.link(self.config.ps_profile, self.env.PS_PROFILE)
