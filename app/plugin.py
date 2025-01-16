"""Plugins interface for managing the functionality of a machine."""

__all__ = ["Plugin"]

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

import rich

from app import cli, models
from app.models import PluginException

C = TypeVar("C", bound=Optional[models.ConfigProtocol])
E = TypeVar("E", bound=Optional[models.EnvironmentProtocol])


class Plugin(cli.Command, models.PluginProtocol, Generic[C, E], ABC):
    """Abstract base class for plugins."""

    @property
    def config(self) -> C:
        return self._config

    @config.setter
    def config(self, value: C) -> None:
        self._config = value

    @property
    def env(self) -> E:
        return self._env

    @env.setter
    def env(self, value: E) -> None:
        self._env = value

    def __init__(self, configuration: C, environment: E) -> None:
        """Initialize the plugin."""
        if not self.is_supported():
            raise PluginException(f"{self.name} is not supported.")
        self.config = configuration
        self.env = environment
        cli.Command.__init__(self)

    @classmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""
        return True

    @abstractmethod
    def setup(self) -> None:
        """Set up the plugin."""

    def status(self) -> None:
        """Print the status of the plugin."""
        is_supported = (
            "[bold green]supported[/]"
            if self.is_supported()
            else "[bold red]not supported[/]"
        )
        rich.print(f"{self.name} is {is_supported}.")
