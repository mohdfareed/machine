"""Package manager interface for installing and managing software packages."""

__all__ = ["PackageManager"]

import shutil
from abc import ABC, abstractmethod
from typing import Callable, List, TypeVar, Union

import rich
import rich.progress
import rich.status
import typer

from app import utils
from app.models import PackageManagerException

T = TypeVar("T", bound="PackageManager")


class PackageManager(ABC):
    """Abstract base class for package managers."""

    shell = utils.Shell()

    @property
    def name(self) -> str:
        """The package manager name."""
        return self.__class__.__name__

    @property
    def command(self) -> str:
        """The package manager's shell command."""
        return self.name.lower()

    @classmethod
    def available_managers(cls) -> List["PackageManager"]:
        """Return a list of available package manager instances."""
        return [
            manager() for manager in cls.__subclasses__() if manager().is_available()
        ]

    @classmethod
    def from_spec(cls, spec: "PackageSpec") -> None:
        """Install a package manager from a specification."""
        for pkg_manager, installer in spec:
            if pkg_manager().is_supported():
                installer()
                return
        raise PackageManagerException("No package manager found.")

    def app(self) -> typer.Typer:
        """Create a Typer app for the package manager."""
        manager_app = typer.Typer(
            name=self.name.lower(), help=f"{self.name} package manager."
        )

        manager_app.command()(self.setup)
        manager_app.command()(self.update)
        manager_app.command()(self.install)
        manager_app.command()(self.uninstall)
        manager_app.command()(self.cleanup)
        manager_app.command(name="status")(self.print_status)
        return manager_app

    def validate(self) -> None:
        """Validate the package manager."""
        if not self.is_supported():
            raise PackageManagerException(f"{self.name} is not supported.")

    def is_available(self) -> bool:
        """Check if the package manager is available."""
        return shutil.which(self.command) is not None

    def setup(self: T) -> T:
        """Install or update the package manager."""
        self.validate()
        if self.is_available():
            utils.LOGGER.debug("%s is already available.", self.name)
            return self

        utils.LOGGER.info("Setting up %s...", self.name)
        with rich.status.Status("[bold green]Setting up..."):
            self._setup()

        self.update()
        utils.LOGGER.debug("%s was set up successfully.", self.name)
        return self

    def update(self: T) -> T:
        """Update the package manager and its packages."""
        self.validate()
        self.setup()

        utils.LOGGER.info("Updating %s...", self.name)
        with rich.status.Status("[bold green]Updating..."):
            self._update()
        utils.LOGGER.debug("%s was updated successfully.", self.name)
        return self

    def install(self: T, packages: str, **kwargs: bool) -> T:
        """Install packages."""
        self.validate()
        self.setup()

        pkgs = packages.split()
        for i in rich.progress.track(
            range(len(pkgs)), description="Installing...", transient=True
        ):
            utils.LOGGER.info("Installing %s using %s...", pkgs[i], self.name)
            self._install(pkgs[i], **kwargs)
            utils.LOGGER.debug("%s was installed successfully.", pkgs[i])
        return self

    def uninstall(self: T, packages: str, **kwargs: bool) -> T:
        """Uninstall packages."""
        self.validate()
        self.setup()

        pkgs = packages.split()
        for i in rich.progress.track(
            range(len(pkgs)), description="Uninstalling...", transient=True
        ):
            utils.LOGGER.info("Uninstalling %s using %s...", pkgs[i], self.name)
            self._uninstall(pkgs[i], **kwargs)
            utils.LOGGER.debug("%s was uninstalled successfully.", pkgs[i])
        return self

    def cleanup(self: T) -> T:
        """Cleanup the package manager."""
        self.validate()
        self.setup()

        utils.LOGGER.info("Cleaning up %s...", self.name)
        with rich.status.Status("[bold green]Cleaning up..."):
            self._cleanup()
        utils.LOGGER.debug("%s was cleaned up successfully.", self.name)
        return self

    def print_status(self) -> None:
        """Print the status of the package manager."""
        status = (
            "[bold green]available[/]"
            if self.is_available()
            else "[bold red]not available[/]"
        )
        rich.print(f"{self.name} is {status}.")

    @abstractmethod
    def is_supported(self) -> bool:
        """Check if the package manager is supported."""

    @abstractmethod
    def _setup(self) -> None:
        """Package manager-specific setup steps."""

    @abstractmethod
    def _update(self) -> None:
        """Package manager-specific update steps."""

    def _install(self, package: str) -> None:
        """Package manager-specific install command."""
        self.shell.execute(f"{self.command} install {package}")

    def _uninstall(self, package: str) -> None:
        """Package manager-specific uninstall command."""
        self.shell.execute(f"{self.command} uninstall {package}")

    def _cleanup(self) -> None:
        """Package manager-specific cleanup command."""
        return None


PackageSpec = list[
    tuple[type[PackageManager], Callable[[], Union[PackageManager, None]]]
]
