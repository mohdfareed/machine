"""App models."""

__all__ = [
    "ConfigProtocol",
    "EnvironmentProtocol",
    "CommandProtocol",
    "PkgManagerProtocol",
    "MachineProtocol",
    "CLIException",
    "PluginException",
    "PkgManagerException",
    "MachineException",
]

from abc import abstractmethod
from typing import Protocol, runtime_checkable

import typer

# MARK: Protocols


@runtime_checkable
class ConfigProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Configuration protocol. Defines what configuration files are needed."""

    @abstractmethod
    def __init__(self) -> None: ...


@runtime_checkable
class EnvironmentProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Environment protocol. Defines what environment variables are needed."""


@runtime_checkable
class CommandProtocol(Protocol):
    """CLI protocol. Defines a CLI interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The plugin name."""

    @property
    @abstractmethod
    def help(self) -> str:
        """The plugin help message."""

    @abstractmethod
    def app(self) -> typer.Typer:
        """Create a Typer app for a CLI command.
        The app will create commands for public methods. Methods can be hidden
        using `@utils.hidden` decorator.
        """


@runtime_checkable
class DebugCommandProtocol(CommandProtocol, Protocol):
    """Debug CLI command. Only available in debug mode."""


@runtime_checkable
class PluginProtocol(CommandProtocol, Protocol):
    """Plugin protocol. Defines the plugin's app interface."""

    @abstractmethod
    def __init__(self, config: ConfigProtocol, env: EnvironmentProtocol) -> None: ...

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


@runtime_checkable
class PkgManagerProtocol(PluginProtocol, Protocol):
    """Package manager protocol. Defines the package manager's interface."""

    @abstractmethod
    def __init__(self) -> None: ...

    @property
    @abstractmethod
    def command(self) -> str:
        """The package manager's shell command."""

    @classmethod
    @abstractmethod
    def is_installed(cls) -> bool:
        """Check if the package manager is available on the system."""

    @abstractmethod
    def install(self, package: str) -> None:
        """Install a package."""

    @abstractmethod
    def update(self) -> None:
        """Update the package manager and its packages."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup the package manager."""


@runtime_checkable
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


class PkgManagerException(Exception):
    """Base exception for package manager errors."""


class MachineException(Exception):
    """Base exception for machine errors."""
