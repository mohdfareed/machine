"""App models."""

__all__ = [
    "ConfigProtocol",
    "EnvironmentProtocol",
    "CommandProtocol",
    "PluginProtocol",
    "PackageManagerProtocol",
    "MachineProtocol",
    "CLIException",
    "PluginException",
    "PackageManagerException",
    "MachineException",
]

from abc import abstractmethod
from typing import Protocol

import typer

# MARK: Protocols


class ConfigProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Configuration protocol. Defines what configuration files are needed."""


class EnvironmentProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Environment protocol. Defines what environment variables are needed."""


class CommandProtocol(Protocol):
    """CLI protocol. Defines a CLI interface.
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
    def app(cls, instance: "CommandProtocol") -> typer.Typer:
        """Create a Typer app for a CLI command."""


class PluginProtocol(CommandProtocol, Protocol):
    """Plugin protocol. Defines the plugin's app interface."""

    @property
    @abstractmethod
    def config(self) -> ConfigProtocol:
        """The plugin configuration files."""

    @property
    @abstractmethod
    def env(self) -> EnvironmentProtocol:
        """The plugin environment variables."""

    @classmethod
    @abstractmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""

    @abstractmethod
    def setup(self) -> None:
        """Set up the plugin."""

    @abstractmethod
    def status(self) -> None:
        """Print the status of the plugin."""

    @abstractmethod
    def __init__(
        self, configuration: ConfigProtocol, environment: EnvironmentProtocol
    ) -> None: ...


class PackageManagerProtocol(PluginProtocol, Protocol):
    """Package manager protocol. Defines the package manager's interface."""

    @property
    @abstractmethod
    def command(self) -> str:
        """The package manager's shell command."""

    @abstractmethod
    def install(self, package: str) -> None:
        """Install a package."""

    @abstractmethod
    def update(self) -> None:
        """Update the package manager and its packages."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup the package manager."""

    @abstractmethod
    def __init__(self) -> None: ...


class MachineProtocol(PluginProtocol, Protocol):
    """Machine protocol. Defines the machine's interface."""

    @property
    @abstractmethod
    def plugins(self) -> list[type[PluginProtocol]]:
        """The machine's plugins."""

    @abstractmethod
    def __init__(self) -> None: ...


# MARK: Exceptions


class CLIException(Exception):
    """Plugin exception."""


class PluginException(Exception):
    """Plugin exception."""


class PackageManagerException(Exception):
    """Base exception for package manager errors."""


class MachineException(Exception):
    """Base exception for machine errors."""
