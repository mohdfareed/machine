"""VSCode setup module."""

import shutil
from pathlib import Path

import typer

from app import utils
from app.plugins.pkg_managers import Brew, SnapStore, Winget
from app.plugins.plugin import Configuration, Environment, Plugin, SetupFunc
from app.utils import LOGGER


class VSCodeConfig(Configuration):
    """VSCode configuration files."""

    vscode: Path
    """The path to the VSCode user settings directory."""


class VSCodeEnv(Environment):
    """VSCode environment variables."""

    VSCODE: Path
    """The path to the VSCode user settings directory."""


class VSCode(Plugin[VSCodeConfig, VSCodeEnv]):
    """Configure VSCode."""

    @property
    def plugin_setup(self) -> SetupFunc:
        return self._setup

    def app(self) -> typer.Typer:
        plugin_app = super().app()
        plugin_app.command()(self.setup_tunnels)
        return plugin_app

    def _setup(self) -> None:
        LOGGER.info("Setting up VSCode...")
        utils.install_from_specs(
            [
                (Brew, lambda: Brew().install("visual-studio-code", cask=True)),
                (Winget, lambda: Winget().install("Microsoft.VisualStudioCode")),
                (SnapStore, lambda: SnapStore().install("code", classic=True)),
            ]
        )

        for file in self.config.vscode.iterdir():
            utils.link(file, self.env.VSCODE / file.name)
        LOGGER.debug("VSCode was setup successfully.")

    def setup_tunnels(self, name: str) -> None:
        """Setup VSCode SSH tunnels as a service."""
        if not shutil.which("code"):
            LOGGER.error("VSCode is not installed.")
            raise typer.Abort

        LOGGER.info("Setting up VSCode SSH tunnels...")
        cmd = (
            f"code tunnel service install "
            f"--accept-server-license-terms --name {name}"
        )
        self.shell.execute(cmd, info=True)
        LOGGER.debug("VSCode SSH tunnels were setup successfully.")
