"""App models."""

from abc import abstractmethod
from typing import Protocol

# MARK: Protocols


class ConfigProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Configuration protocol. Defines what configuration files are needed."""


class EnvironmentProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Environment protocol. Defines what environment variables are needed."""


class PluginProtocol(Protocol):
    """Plugin protocol. Defines the plugin's app interface.
    Member functions not starting with an underscore are automatically
    added as commands.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The plugin name."""

    @property
    @abstractmethod
    def help(self) -> str:
        """The plugin help message."""

    @classmethod
    @abstractmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""

    @abstractmethod
    def status(self) -> None:
        """Print the status of the plugin."""


class PackageManagerProtocol(PluginProtocol, Protocol):
    """Package manager protocol. Defines the package manager's interface."""

    @property
    @abstractmethod
    def command(self) -> str:
        """The package manager's shell command."""

    @classmethod
    @abstractmethod
    def is_installed(cls, instance: "PackageManagerProtocol") -> bool:
        """Check if the package manager is installed."""

    @abstractmethod
    def install(self, package: str) -> None:
        """Install a package."""

    @abstractmethod
    def setup(self) -> None:
        """Setup the package manager."""

    @abstractmethod
    def update(self) -> None:
        """Update the package manager and its packages."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup the package manager."""


class MachineProtocol(PluginProtocol, Protocol):
    """Machine protocol. Defines the machine's interface."""

    @abstractmethod
    def setup(self) -> None:
        """Setup the machine."""


# MARK: Exceptions


class PluginException(Exception):
    """Plugin exception."""


class PackageManagerException(Exception):
    """Base exception for package manager errors."""


class MachineException(Exception):
    """Base exception for machine errors."""
