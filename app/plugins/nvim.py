"""NeoVim setup module."""

from pathlib import Path

from app import utils
from app.plugins.pkg_managers import APT, Brew, SnapStore, Winget
from app.plugins.plugin import Configuration, Environment, Plugin, SetupFunc
from app.utils import LOGGER


class NeoVimConfig(Configuration):
    """NeoVim configuration files."""

    vim: Path


class NeoVimEnv(Environment):
    """NeoVim environment variables."""

    VIM: Path


class NeoVim(Plugin[NeoVimConfig, NeoVimEnv]):
    """Install NeoVim on a machine."""

    @property
    def plugin_setup(self) -> SetupFunc:
        return self._setup

    def _setup(self) -> None:
        if Brew().is_supported():
            Brew().install("nvim lazygit ripgrep fd")

        elif Winget().is_supported():
            Winget().install(
                "Neovim.Neovim JesseDuffield.lazygit BurntSushi.ripgrep sharkdp.fd"
            )

        elif SnapStore().is_supported():
            SnapStore().install("nvim lazygit-gm ")
            SnapStore().install("ripgrep", classic=True)
            APT().install("fd-find")

        utils.link(self.config.vim, self.env.VIM)
        LOGGER.debug("NeoVim setup complete.")
