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
        return type(self).__name__

    @property
    def help(self) -> str:
        return type(self).__doc__ or f"{self.name} plugin."

    @utils.hidden
    def app(self) -> typer.Typer:
        plugin_app = typer.Typer(name=self.name.lower(), help=self.help)
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if method == getattr(type(self), name):
                continue  # skip class methods
            if name.startswith("_"):
                continue  # skip private methods
            if utils.is_hidden(method):
                continue  # skip hidden methods
            plugin_app.command(name)(method)
        return plugin_app
