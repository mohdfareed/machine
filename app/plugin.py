"""Plugins interface for managing the functionality of a machine."""

__all__ = ["Plugin"]

import inspect
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

import rich
import typer

from app import models, utils
from app.models import PluginException

C = TypeVar("C", bound=Optional[models.ConfigProtocol])
E = TypeVar("E", bound=Optional[models.EnvironmentProtocol])


class Plugin(ABC, models.PluginProtocol, Generic[C, E]):
    """Abstract base class for plugins."""

    @property
    def name(self) -> str:
        """The plugin name."""
        return type(self).__name__

    @property
    def help(self) -> str:
        """The plugin help message."""
        return type(self).__doc__ or f"{self.name} plugin."

    def __init__(self, configuration: C, environment: E) -> None:
        """Initialize the plugin."""
        if not self.is_supported():
            raise PluginException(f"{self.name} is not supported.")
        self.config = configuration
        self.env = environment

    @classmethod
    def app(cls, instance: models.PluginProtocol) -> typer.Typer:
        """Create a Typer app for the plugin."""
        plugin_app = typer.Typer(name=instance.name.lower(), help=instance.help)
        for name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
            # skip class methods
            if method == getattr(cls, name):
                continue
            # skip private methods
            if not name.startswith("_"):
                plugin_app.command(name)(method)

        utils.LOGGER.debug("Created plugin: %s", instance.name)
        return plugin_app

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
