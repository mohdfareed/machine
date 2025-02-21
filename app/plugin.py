"""Plugins interface for managing the functionality of a machine."""

__all__ = ["Plugin"]

import inspect
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import typer

from app import models, utils

C = TypeVar("C", bound=models.ConfigProtocol)
E = TypeVar("E", bound=models.EnvProtocol)


class Plugin(models.PluginProtocol, Generic[C, E], ABC):
    """Abstract base class for plugins."""

    @property
    def name(self) -> str:
        """The name of the plugin."""
        return type(self).__name__

    @property
    def help(self) -> str:
        """The help message for the plugin."""
        return type(self).__doc__ or f"{self.name} plugin."

    def __init__(self, config: C, env: E) -> None:
        if not self.is_supported():
            raise models.AppError(f"{self.name} is not supported.")
        self.config: C = config
        self.env: E = env

    @classmethod
    def is_supported(cls) -> bool:
        return True

    @utils.hidden
    def app(self) -> typer.Typer:
        plugin_app = typer.Typer(name=self.name.lower(), help=self.help)
        for name, method in inspect.getmembers(
            self, predicate=inspect.ismethod
        ):

            if method == getattr(type(self), name, None):
                continue  # skip class methods
            if name.startswith("_"):
                continue  # skip private methods
            if utils.is_hidden(method):
                continue  # skip hidden methods

            plugin_app.command(name=name)(method)
        return plugin_app

    def setup(self) -> None:
        utils.LOGGER.info("Setting up %s...", self.name)
        utils.loading_indicator(f"Setting up {self.name}")(self._setup)()
        utils.LOGGER.info("Finished setting up %s.", self.name)

    @utils.hidden
    @abstractmethod
    def _setup(self) -> None:
        """Set up the plugin."""
