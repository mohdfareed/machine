"""App models."""

__all__ = [
    "ConfigProtocol",
    "EnvProtocol",
    "PluginProtocol",
    "PkgManagerProtocol",
    "MachineProtocol",
    "AppError",
]

from abc import abstractmethod
from typing import Protocol, runtime_checkable

import typer


@runtime_checkable
class ConfigProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Configuration protocol. Defines configuration files."""


@runtime_checkable
class EnvProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Environment protocol. Defines environment variables."""


@runtime_checkable
class PluginProtocol(Protocol):
    """Plugin protocol. Defines a plugin that can be set up on a machine."""

    @abstractmethod
    def __init__(
        self,
        config: ConfigProtocol,
        env: EnvProtocol,
    ) -> None: ...

    @classmethod
    @abstractmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""

    @abstractmethod
    def setup(self) -> None:
        """Set up the plugin."""

    @abstractmethod
    def app(self) -> typer.Typer:
        """Create a Typer app for the plugin.

        The app will create commands for public methods. Methods can be hidden
        using `@utils.hidden` decorator.
        """


@runtime_checkable
class PkgManagerProtocol(PluginProtocol, Protocol):
    """Package manager protocol. Defines the package manager's interface."""

    @abstractmethod
    def __init__(self) -> None: ...

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
    def status(self) -> None:
        """Print the status of the package manager."""


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


class AppError(Exception):
    """An application error exception."""
