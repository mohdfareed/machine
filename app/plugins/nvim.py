"""NeoVim setup module."""

__all__ = ["NeoVim"]

from pathlib import Path
from typing import Protocol

from app import models, utils
from app.plugins.pkg_managers import APT, Brew, SnapStore, Winget
from app.plugins.plugin import Plugin
from app.utils import LOGGER


class NeoVimConfig(models.ConfigProtocol, Protocol):
    """NeoVim configuration files."""

    vim: Path


class NeoVimEnv(models.EnvironmentProtocol, Protocol):
    """NeoVim environment variables."""

    VIM: Path


class NeoVim(Plugin[NeoVimConfig, NeoVimEnv]):
    """Install NeoVim on a machine."""

    def setup(self) -> None:
        """Set up NeoVim."""

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
