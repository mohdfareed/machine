"""VSCode setup module."""

__all__ = ["VSCode"]

import shutil
from pathlib import Path
from typing import Protocol

import typer

from app import models, utils
from app.plugins.pkg_managers import Brew, SnapStore, Winget, install_from_specs
from app.plugins.plugin import Plugin
from app.utils import LOGGER


class VSCodeConfig(models.ConfigProtocol, Protocol):
    """VSCode configuration files."""

    vscode: Path
    """The path to the VSCode user settings directory."""


class VSCodeEnv(models.EnvironmentProtocol, Protocol):
    """VSCode environment variables."""

    VSCODE: Path
    """The path to the VSCode user settings directory."""


class VSCode(Plugin[VSCodeConfig, VSCodeEnv]):
    """Configure VSCode."""

    shell = utils.Shell()

    def setup(self) -> None:
        """Set up VSCode."""
        LOGGER.info("Setting up VSCode...")
        install_from_specs(
            [
                (Brew, lambda: Brew().install_cask("visual-studio-code")),
                (Winget, lambda: Winget().install("Microsoft.VisualStudioCode")),
                (SnapStore, lambda: SnapStore().install_classic("code")),
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
