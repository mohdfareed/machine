"""Shell setup module."""

__all__ = ["ZSH", "PowerShell", "NeoVim", "Btop"]

from pathlib import Path
from typing import Any, Protocol

import typer

from app import models, utils
from app.plugin import Plugin
from app.plugins.pkg_managers import APT, Brew, Scoop, SnapStore, Winget
from app.utils import LOGGER

# region: ZSH

ZSHENV_TEMPLATE = """
export MACHINE="{machine}"
export MACHINE_ID="{machine_id}"
source "{machine_zshenv}"
"""


class ZSHConfig(models.ConfigProtocol, Protocol):
    """Shell configuration."""

    machine_id: str
    machine: Path

    zshenv: Path
    zshrc: Path
    tmux_config: Path


class ZSHEnv(models.EnvProtocol, Protocol):
    """Shell environment."""

    ZSHENV: Path
    ZSHRC: Path
    TMUX_CONFIG: Path


class ZSH(Plugin[ZSHConfig, ZSHEnv]):
    """Configure ZSH shell."""

    shell = utils.Shell()

    @classmethod
    def is_supported(cls) -> bool:
        return not utils.Platform.WINDOWS

    def _setup(self) -> None:
        if Brew.is_supported():
            Brew().install("zsh tmux bat eza")
        elif APT.is_supported():
            APT().install("zsh tmux bat eza")
        else:
            utils.LOGGER.error("No supported package manager found.")
            raise typer.Abort

        # create machine identifier
        zshenv_content = ZSHENV_TEMPLATE.format(
            machine=self.config.machine,
            machine_id=self.config.machine_id,
            machine_zshenv=self.config.zshenv,
        )
        self.env.ZSHENV.write_text(zshenv_content)

        # symlink config files
        utils.link(self.config.zshrc, self.env.ZSHRC)
        utils.link(self.config.tmux_config, self.env.TMUX_CONFIG)

        # update zinit and its plugins
        self.update_zinit()

        # clean up
        LOGGER.debug("Cleaning up...")
        self.shell.execute(
            "sudo rm -rf ~/.zcompdump* ~/.zshrc ~/.zsh_sessions ~/.zsh_history ~/.lesshst",
            throws=False,
        )

    @utils.loading_indicator("Updating zinit")
    def update_zinit(self) -> None:
        """Update zinit and its plugins."""
        LOGGER.info("Updating zinit and its plugins...")
        source_env = (
            f"source {self.config.zshenv} && source {self.config.zshrc}"
        )
        self.shell.execute(
            f"{source_env} && zinit self-update && zinit update"
        )
        LOGGER.debug("Zinit update complete.")


# endregion

# region: PowerShell

PS_PROFILE_TEMPLATE = """
$env:MACHINE="{machine}"
$env:MACHINE_ID="{machine_id}"
. "{machine_ps_profile}"
"""


class PowerShellConfig(models.ConfigProtocol, Protocol):
    """PowerShell configuration files."""

    machine_id: str
    machine: Path
    ps_profile: Path


class PowerShellEnv(models.EnvProtocol, Protocol):
    """PowerShell environment variables."""

    PS_PROFILE: Path


class PowerShell(Plugin[PowerShellConfig, PowerShellEnv]):
    """Install PowerShell on a machine."""

    def _setup(self) -> None:
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


# endregion
# region: Tools


class NeoVimConfig(models.ConfigProtocol, Protocol):
    """NeoVim configuration files."""

    vim: Path


class NeoVimEnv(models.EnvProtocol, Protocol):
    """NeoVim environment variables."""

    VIM: Path


class NeoVim(Plugin[NeoVimConfig, NeoVimEnv]):
    """Install NeoVim on a machine."""

    def _setup(self) -> None:
        if Brew.is_supported():
            Brew().install("nvim lazygit ripgrep fd")

        elif Winget.is_supported():
            Winget().install(
                "Neovim.Neovim JesseDuffield.lazygit BurntSushi.ripgrep sharkdp.fd"
            )

        elif SnapStore.is_supported():
            SnapStore().install("nvim lazygit-gm ")
            SnapStore().install_classic("ripgrep")
            APT().install("fd-find")

        utils.link(self.config.vim, self.env.VIM)
        LOGGER.debug("NeoVim setup complete.")


class Btop(Plugin[Any, Any]):
    """Install Btop on a machine."""

    def _setup(self) -> None:
        if Brew.is_supported():
            Brew().install("btop")
        elif SnapStore.is_supported():
            SnapStore().install("btop")
        elif Scoop.is_supported():
            Scoop().install("btop-lhm")


# endregion
