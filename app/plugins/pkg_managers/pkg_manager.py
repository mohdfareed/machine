"""Package manager interface for installing and managing software packages."""

__all__ = ["PkgManager"]

import shutil
from abc import ABC

import rich
import typer

from app import models, utils
from app.models import PackageManagerException
from app.plugins import plugin

PkgManagerPlugin = plugin.Plugin[models.ConfigFiles, models.Environment]


class PkgManager(PkgManagerPlugin, ABC):
    """Abstract base class for package managers."""

    is_setup = False

    @property
    def command(self) -> str:
        """The package manager's shell command."""
        return self.name.lower()

    @property
    def plugin_setup(self) -> plugin.SetupFunc:
        """Package manager-specific setup steps."""
        return self.setup

    def __init__(self) -> None:  # pylint: disable=super-init-not-called
        """Initialize the package manager."""
        if self.is_setup:
            return

        if not self.is_supported():
            raise PackageManagerException(f"{self.name} is not supported.")

        # cleanup
        utils.post_install_tasks.append(self._cleanup)
        self.is_setup = True

    def app(self) -> typer.Typer:
        """Create a Typer app for the package manager."""

        manager_app = super().app()
        manager_app.command()(self.update)
        manager_app.command()(self.install)
        manager_app.command()(self.cleanup)
        return manager_app

    def is_available(self) -> bool:
        """Check if the package manager is available on the system."""
        return shutil.which(self.command) is not None

    def setup(self) -> None:
        """Package manager-specific setup steps."""

    def update(self) -> None:
        """Package manager-specific update steps."""

    @utils.install_with_progress("Installing...")
    def install(self, package: str) -> None:
        """Package manager-specific install command."""
        self.shell.execute(f"{self.command} install {package}")

    @utils.install_with_progress("Uninstalling...")
    def uninstall(self, package: str) -> None:
        """Package manager-specific Uninstall command."""
        self.shell.execute(f"{self.command} uninstall {package}")

    def cleanup(self) -> None:
        """Package manager-specific cleanup command. Optional."""

    def print_status(self) -> None:
        """Print the status of the plugin."""

        is_supported = (
            "[bold green]supported[/]"
            if self.is_supported()
            else "[bold red]not supported[/]"
        )

        is_available = (
            "[bold green]available[/]"
            if self.is_available()
            else "[bold red]not available[/]"
        )

        rich.print(f"{self.name} is {is_supported} and {is_available}.")

    def _cleanup(self) -> None:
        utils.LOGGER.info("Cleaning up %s...", self.name)
        utils.with_status("Cleaning up...")(self.cleanup)()
        utils.LOGGER.debug("%s was cleaned up successfully.", self.name)

    def _setup(self) -> None:
        utils.LOGGER.info("Setting up %s...", self.name)
        utils.with_status("Setting up...")(self.plugin_setup)()
        utils.LOGGER.debug("%s was set up successfully.", self.name)
