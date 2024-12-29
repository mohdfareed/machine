"""Shell setup module."""

__all__ = ["Shell", "ShellConfig", "ShellEnv"]

from pathlib import Path

import rich.status

from app import config, utils
from app.plugins.pkg_managers import APT, Brew
from app.plugins.plugin import Configuration, Environment, Plugin, SetupFunc
from app.utils import LOGGER

ZSHENV_TEMPLATE = f"""
export MACHINE="{config.Machine().machine}"
export MACHINE_ID={{machine_id}}
source {{machine_zshenv}}
"""

PS_PROFILE_TEMPLATE = f"""
$env:MACHINE="{config.Machine().machine}"
$env:MACHINE_ID={{machine_id}}
. {{machine_zshenv}}
"""


class ShellConfig(Configuration):
    """Shell configuration."""

    zshenv: Path
    zshrc: Path
    tmux_config: Path
    ps_profile: Path


class ShellEnv(Environment):
    """Shell environment."""

    ZSHENV: Path
    ZSHRC: Path
    TMUX_CONFIG: Path
    PS_PROFILE: Path


class Shell(Plugin[ShellConfig, ShellEnv]):
    """Configure ZSH shell."""

    @property
    def plugin_setup(self) -> SetupFunc:
        return self._setup

    @classmethod
    def is_supported(cls) -> bool:
        return not utils.WINDOWS

    def _setup(self) -> None:
        LOGGER.info("Setting up shell...")
        utils.install_from_specs(
            [
                (Brew, lambda: Brew().install("zsh tmux eza bat")),
                (APT, lambda: APT().install("zsh tmux bat eza")),
            ]
        )

        # symlink config files
        utils.link(self.config.zshenv, self.env.ZSHENV)
        utils.link(self.config.zshrc, self.env.ZSHRC)
        utils.link(self.config.tmux_config, self.env.TMUX_CONFIG)
        utils.link(self.config.ps_profile, self.env.PS_PROFILE)

        # update zinit and its plugins
        LOGGER.info("Updating zinit and its plugins...")
        source_env = f"source {self.config.zshenv} && source {self.config.zshrc}"
        with rich.status.Status("[bold green]Updating..."):
            self.shell.execute(f"{source_env} && zinit self-update && zinit update")

        # clean up
        LOGGER.debug("Cleaning up...")
        self.shell.execute(
            "sudo rm -rf ~/.zcompdump* ~/.zshrc ~/.zsh_sessions ~/.zsh_history ~/.lesshst",
            throws=False,
        )
        LOGGER.debug("Shell setup complete.")
