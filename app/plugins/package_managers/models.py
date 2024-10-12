"""Package manager interface for installing and managing software packages."""

__all__ = ["PackageManager", "PackageManagerException"]

import shutil
from abc import ABC, abstractmethod
from typing import Generator

from app import utils


class PackageManager(ABC):
    """Abstract base class for package managers."""

    shell = utils.Shell()

    @classmethod
    def name(cls) -> str:
        """The package manager name."""
        return cls.__name__

    @classmethod
    def command(cls) -> str:
        """The package manager's shell command."""
        return cls.name().lower()

    @classmethod
    def is_available(cls) -> bool:
        """Check if the package manager is available."""
        return shutil.which(cls.command()) is not None

    @classmethod
    @abstractmethod
    @utils.setup_wrapper
    def setup(cls) -> None:
        """Install or update the package manager."""

    @classmethod
    @abstractmethod
    @utils.update_wrapper
    def update(cls) -> None:
        """Update the package manager and its packages."""

    @classmethod
    @utils.install_wrapper
    def install(cls, package: str) -> None:
        """Install a package."""
        cls.shell.execute(f"{cls.command()} install {package}")

    @classmethod
    @utils.uninstall_wrapper
    def uninstall(cls, package: str) -> None:
        """Install a package."""
        cls.shell.execute(f"{cls.command()} uninstall {package}")

    @classmethod
    @utils.cleanup_wrapper
    def cleanup(cls) -> None:
        """Cleanup package manager."""
        return None

    @classmethod
    @abstractmethod
    @utils.is_supported_wrapper
    def is_supported(cls) -> bool:
        """Check if the package manager is supported."""

    @staticmethod
    def available(
        *managers: type["PackageManager"],
    ) -> Generator[type["PackageManager"], None, None]:
        """Return a list of available package managers."""
        yield from (manager for manager in managers if manager.is_available())


class PackageManagerException(Exception):
    """Base exception for package manager errors."""
