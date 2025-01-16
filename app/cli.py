"""CLI interface for managing the Typer app."""

__all__ = ["Command"]

import inspect
from abc import ABC

import typer

from app import models, utils


class Command(models.CommandProtocol, ABC):
    """Abstract base class for CLI command apps."""

    @property
    def name(self) -> str:
        """The plugin name."""
        return type(self).__name__

    @property
    def help(self) -> str:
        """The plugin help message."""
        return type(self).__doc__ or f"{self.name} plugin."

    @classmethod
    def app(cls, instance: models.CommandProtocol) -> typer.Typer:
        """Create a Typer app for a CLI command."""
        plugin_app = typer.Typer(name=instance.name.lower(), help=instance.help)
        for name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
            # skip class methods
            if method == getattr(cls, name):
                continue
            # skip private methods
            if not name.startswith("_"):
                plugin_app.command(name)(method)

        utils.LOGGER.debug("Created app: %s", instance.name)
        return plugin_app
