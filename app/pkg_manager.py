"""Package manager interface for installing and managing software packages."""

__all__ = ["PkgManagerPlugin"]

import shutil
from abc import ABC, abstractmethod

import rich
import typer
from typing_extensions import override

from app import config, env, plugin, utils
from app.models import PackageManagerException, PackageManagerProtocol

Plugin = plugin.Plugin[config.MachineConfig, env.MachineEnv]


class PkgManagerPlugin(
    Plugin, PackageManagerProtocol, ABC
):  # pylint: disable=too-many-ancestors
    """Abstract base class for package managers."""

    shell = utils.Shell()
    is_setup = False
    is_cleaned_up = False

    @property
    def command(self) -> str:
        """The package manager's shell command."""
        return self.name.lower()

    def __init__(self) -> None:
        self.config: config.MachineConfig
        self.env: env.MachineEnv
        if not self.is_supported():
            raise PackageManagerException(f"{self.name} is not supported.")
        super().__init__(config.MachineConfig(), env.OS_ENV())

    @classmethod
    def manager_app(cls) -> typer.Typer:
        """Create a Typer app for the package manager."""
        instance = cls()
        return cls.app(instance)

    def setup(self) -> None:
        if type(self).is_setup:
            return
        type(self).is_setup = True

        utils.post_install_tasks += [self.cleanup]
        if self.is_installed(self):
            return

        utils.LOGGER.info("Setting up %s...", self.name)
        utils.with_status("Setting up...")(self._setup)()
        utils.LOGGER.debug("%s was set up successfully.", self.name)

    def update(self) -> None:
        self.setup()
        utils.LOGGER.info("Updating %s...", self.name)
        utils.with_status("Updating...")(self._update)()
        utils.LOGGER.debug("%s was updated successfully.", self.name)

    def cleanup(self) -> None:
        utils.LOGGER.info("Cleaning up %s...", self.name)
        utils.with_status("Cleaning up...")(self._cleanup)()
        utils.LOGGER.debug("%s was cleaned up successfully.", self.name)

    def install(self, package: str) -> None:
        self.setup()

        def wrapper(packages: list[str]) -> None:
            utils.LOGGER.info("Installing %s...", packages)
            self._install(" ".join(packages))
            utils.LOGGER.debug("%s was installed successfully.", packages)

        utils.with_progress("Installing...")(wrapper)(package.split())

    @override
    def status(self) -> None:
        is_supported = (
            "[bold green]supported[/]"
            if self.is_supported()
            else "[bold red]not supported[/]"
        )
        is_installed = (
            "[bold green]installed[/]"
            if self.is_installed(self)
            else "[bold red]not installed[/]"
        )
        rich.print(f"{self.name} is {is_supported} and {is_installed}.")

    @abstractmethod
    def _setup(self) -> None:
        """Package manager-specific setup command."""

    @abstractmethod
    def _update(self) -> None:
        """Package manager-specific update steps."""

    @abstractmethod
    def _cleanup(self) -> None:
        """Package manager-specific cleanup command."""

    @abstractmethod
    def _install(self, package: str) -> None:
        """Package manager-specific install command."""

    @staticmethod
    def is_installed(instance: PackageManagerProtocol) -> bool:
        """Check if the package manager is available on the system."""
        return shutil.which(instance.command) is not None
