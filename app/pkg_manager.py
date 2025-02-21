"""Package manager interface for installing and managing software packages."""

__all__ = ["PkgManagerPlugin"]

import shutil
from abc import ABC, abstractmethod

import rich
from typing_extensions import override

from app import models, plugin, utils


class PkgManagerPlugin(
    plugin.Plugin[None, None], models.PkgManagerProtocol, ABC
):
    """Abstract base class for package managers."""

    @property
    def command(self) -> str:
        """The package manager's command."""
        return self.name.lower()

    def __init__(self) -> None:
        super().__init__(None, None)

    @classmethod
    def is_installed(cls) -> bool:
        return shutil.which(cls().command) is not None

    def setup(self) -> None:
        if not self.is_installed():
            super().setup()

    @utils.loading_indicator("Updating pkg manager")
    def update(self) -> None:
        self.setup()
        utils.LOGGER.info("Updating %s...", self.name)
        self._update()
        utils.LOGGER.debug("Updated %s.", self.name)

    @utils.pkg_installer
    def install(self, package: str) -> None:
        self.setup()
        self._install(package)

    @override
    def status(self) -> None:
        is_supported = (
            "[bold green]supported[/]"
            if self.is_supported()
            else "[bold red]not supported[/]"
        )
        is_installed = (
            "[bold green]installed[/]"
            if self.is_installed()
            else "[bold red]not installed[/]"
        )
        rich.print(f"{self.name} is {is_supported} and {is_installed}.")

    # MARK: Abstract methods

    @utils.hidden
    @abstractmethod
    def _install(self, package: str) -> None:
        """Install a package."""

    @utils.hidden
    @abstractmethod
    def _update(self) -> None:
        """Update the package manager and its packages."""
