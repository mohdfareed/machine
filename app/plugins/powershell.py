"""PowerShell setup module."""

from pathlib import Path

from app import models
from app.plugin import Plugin
from app.plugins.pkg_managers import Brew, SnapStore, Winget

PS_PROFILE_TEMPLATE = """
$env:MACHINE="{machine}"
$env:MACHINE_ID="{machine_id}"
. "{machine_ps_profile}"
"""


class PowerShellConfig(models.ConfigProtocol):
    """PowerShell configuration files."""

    machine_id: str
    machine: Path

    ps_profile: Path


class PowerShellEnv(models.EnvironmentProtocol):
    """PowerShell environment variables."""

    PS_PROFILE: Path


class PowerShell(Plugin[PowerShellConfig, PowerShellEnv]):
    """Install PowerShell on a machine."""

    def setup(self) -> None:
        """Set up PowerShell."""

        if Brew.is_supported():
            Brew().install_cask("powershell")
        elif Winget.is_supported():
            Winget().install("Microsoft.PowerShell")
        elif SnapStore.is_supported():
            SnapStore().install("powershell")

        # create machine identifier
        ps_profile_content = PS_PROFILE_TEMPLATE.format(
            machine=self.config.machine,
            machine_id=self.config.machine_id,
            machine_ps_profile=self.config.ps_profile,
        )

        # create the PowerShell profile
        self.env.PS_PROFILE.parent.mkdir(parents=True, exist_ok=True)
        self.env.PS_PROFILE.write_text(ps_profile_content)
