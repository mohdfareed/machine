"""Package manager interface for installing and managing software packages."""

__all__ = ["PackageManager", "PackageManagerException"]

from abc import ABC, abstractmethod
from typing import Any, Callable, Union

from app import utils
from app.utils import LOGGER


class PackageManager(ABC):
    """Abstract base class for package managers."""

    shell = utils.Shell()

    @property
    def name(self) -> str:
        """The package manager name."""
        return self.__class__.__name__

    def __init__(self) -> None:
        if not self.is_supported():
            raise PackageManagerException(
                f"Package manager {self.name} is not supported."
            )

        LOGGER.info("Setting up %s...", self.name)
        self.setup()
        LOGGER.debug("%s was setup successfully.", self.name)

    @abstractmethod
    def setup(self) -> None:
        """Setup the package manager."""

    @abstractmethod
    def install(self, package: Union[str, list[str]]) -> None:
        """Install a package."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup package manager."""

    @staticmethod
    @abstractmethod
    def is_supported() -> bool:
        """Check if the package manager is supported."""

    @staticmethod
    def installer(func: Callable[..., None]) -> Callable[..., None]:
        """Decorator to wrap installation process."""

        def wrapper(
            self: PackageManager,
            package: Union[str, list[str]],
            *args: Any,
            **kwargs: Any,
        ) -> None:
            if isinstance(package, str):
                package = package.split()

            for pkg in package:
                LOGGER.info("Installing %s from %s...", pkg, self.name)
                func(self, pkg, *args, **kwargs)
                LOGGER.debug("%s was installed successfully.", pkg)

        return wrapper

    def __del__(self) -> None:
        LOGGER.debug("Cleaning up %s...", self.name)
        self.cleanup()
        LOGGER.debug("%s cleanup complete.", self.name)


class PackageManagerException(Exception):
    """Base exception for package manager errors."""
