"""Package manager interface for installing and managing software packages."""

__all__ = ["PkgManagerPlugin"]

import shutil
from abc import ABC, abstractmethod

import rich
from typing_extensions import override

from app import config, env, models, plugin, utils

Plugin = plugin.Plugin[config.MachineConfig, env.MachineEnv]


class PkgManagerPlugin(Plugin, models.PkgManagerProtocol, ABC):
    """Abstract base class for package managers."""

    shell = utils.Shell()
    is_setup = False
    is_cleaned_up = False

    @property
    def command(self) -> str:
        return self.name.lower()

    def __init__(self) -> None:
        if not self.is_supported():
            raise models.PkgManagerException(f"{self.name} is not supported.")
        super().__init__(config.MachineConfig(), env.OSEnvironment())

    @classmethod
    def is_installed(cls) -> bool:
        return shutil.which(cls().command) is not None

    @utils.with_status("Setting up")
    def setup(self) -> None:
        if type(self).is_setup:
            return
        type(self).is_setup = True

        utils.post_install_tasks += [self.cleanup]
        if self.is_installed():
            return
        self._setup()

    def update(self) -> None:
        self.setup()
        utils.with_status(f"Updating {self.name}")(self._update)()

    def cleanup(self) -> None:
        utils.with_status(f"Cleaning up {self.name}")(self._cleanup())

    def install(self, package: str) -> None:
        self.setup()

        def install_package(packages: list[str]) -> None:
            self._install(" ".join(packages))

        utils.with_progress("Installing")(install_package)(package.split())

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
    def _setup(self) -> None:
        """Package manager-specific setup command."""

    @utils.hidden
    @abstractmethod
    def _update(self) -> None:
        """Package manager-specific update steps."""

    @utils.hidden
    @abstractmethod
    def _cleanup(self) -> None:
        """Package manager-specific cleanup command."""

    @utils.hidden
    @abstractmethod
    def _install(self, package: str) -> None:
        """Package manager-specific install command."""
