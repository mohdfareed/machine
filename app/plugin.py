"""Plugins interface for managing the functionality of a machine."""

__all__ = ["Plugin"]

from abc import ABC
from typing import Generic, TypeVar

import rich

from app import cli, models

C = TypeVar("C", bound=models.ConfigProtocol)
E = TypeVar("E", bound=models.EnvironmentProtocol)


class Plugin(cli.Command, models.PluginProtocol, Generic[C, E], ABC):
    """Abstract base class for plugins."""

    def __init__(self, config: C, env: E) -> None:
        """Initialize the plugin."""
        if not self.is_supported():
            raise models.PluginException(f"{self.name} is not supported.")

        self.config: C = config
        self.env: E = env
        cli.Command.__init__(self)

    @classmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""
        return True

    def status(self) -> None:
        """Print the status of the plugin."""
        is_supported = (
            "[bold green]supported[/]"
            if self.is_supported()
            else "[bold red]not supported[/]"
        )
        rich.print(f"{self.name} is {is_supported}.")
