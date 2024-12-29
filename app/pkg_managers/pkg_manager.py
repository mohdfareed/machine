"""Package manager interface for installing and managing software packages."""

__all__ = ["PkgManager"]

import shutil
from abc import ABC
from typing import TypeVar, Union

import rich
import rich.progress
import rich.status
import typer

from app import utils
from app.models import PackageManagerException

T = TypeVar("T", bound="PkgManager")


class PkgManager(ABC):
    """Abstract base class for package managers."""

    is_setup = False
    shell = utils.Shell()

    @property
    def name(self) -> str:
        """The package manager name."""
        return self.__class__.__name__

    @property
    def command(self) -> str:
        """The package manager's shell command."""
        return self.name.lower()

    def __init__(self) -> None:
        """Initialize the package manager."""
        if self.is_setup:
            return

        if not self.is_supported():
            raise PackageManagerException(f"{self.name} is not supported.")

        if self.is_available():
            utils.LOGGER.debug("%s is available.", self.name)
            utils.with_status(f"Updating {self.name}...")(self.update)()
            return

        utils.LOGGER.info("Setting up %s...", self.name)
        utils.with_status("Setting up...")(self.setup)()
        utils.LOGGER.debug("%s was set up successfully.", self.name)
        self.is_setup = True

    def app(self) -> typer.Typer:
        """Create a Typer app for the package manager."""
        manager_app = typer.Typer(
            name=self.name.lower(), help=f"{self.name} package manager."
        )

        manager_app.command()(self.setup)
        manager_app.command()(self.update)
        manager_app.command()(self.install)
        manager_app.command()(self.cleanup)
        manager_app.command(name="status")(self.print_status)
        return manager_app

    def is_available(self) -> bool:
        """Check if the package manager is available on the system."""
        return shutil.which(self.command) is not None

    @classmethod
    def is_supported(cls) -> bool:
        """Check if the package manager is supported."""
        return True

    def setup(self) -> None:
        """Package manager-specific setup steps."""

    def update(self) -> None:
        """Package manager-specific update steps."""

    @utils.install_with_progress("Installing...")
    def install(self, package: Union[list[str], str]) -> None:
        """Package manager-specific install command."""
        self.shell.execute(f"{self.command} install {package}")

    @utils.install_with_progress("Uninstalling...")
    def uninstall(self, package: Union[list[str], str]) -> None:
        """Package manager-specific Uninstall command."""
        self.shell.execute(f"{self.command} uninstall {package}")

    def cleanup(self) -> None:
        """Package manager-specific cleanup command. Optional."""

    def print_status(self) -> None:
        """Print the status of the package manager."""
        is_available = (
            "[bold green]available[/]"
            if self.is_available()
            else "[bold red]not available[/]"
        )

        is_supported = (
            "[bold green]supported[/]"
            if self.is_supported()
            else "[bold red]not supported[/]"
        )

        rich.print(f"{self.name} is {is_available} and {is_supported}.")

    def __del__(self) -> None:
        """Cleanup the package manager."""
        utils.LOGGER.info("Cleaning up %s...", self.name)
        utils.with_status("Cleaning up...")(self.cleanup)()
        utils.LOGGER.debug("%s was cleaned up successfully.", self.name)
