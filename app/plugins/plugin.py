"""Plugins interface for managing the functionality of a machine."""

__all__ = ["Plugin", "SetupFunc"]

from abc import ABC, abstractmethod
from typing import Callable, Generic, Optional, TypeVar

import rich
import typer

from app import models, utils
from app.models import PluginException

C = TypeVar("C", bound=Optional[models.ConfigFiles])
E = TypeVar("E", bound=Optional[models.Environment])

SetupFunc = Callable[..., None]


class Plugin(ABC, Generic[C, E]):
    """Abstract base class for plugins."""

    shell = utils.Shell()

    @property
    def name(self) -> str:
        """The plugin name."""
        return self.__class__.__name__

    @property
    def help(self) -> str:
        """The plugin help message."""
        return type(self).__doc__ or f"{self.name} plugin."

    @property
    @abstractmethod
    def plugin_setup(self) -> SetupFunc:
        """Plugin-specific setup steps."""
        raise NotImplementedError

    def __init__(self, configuration: C, environment: E) -> None:
        """Initialize the plugin."""
        self.config = configuration
        self.env = environment
        if not self.is_supported():
            raise PluginException(f"{self.name} is not supported.")

    def app(self) -> typer.Typer:
        """Create a Typer app for the plugin."""

        manager_app = typer.Typer(name=self.name.lower(), help=self.help)
        manager_app.command(name="setup")(self.plugin_setup)
        manager_app.command(name="status")(self.print_status)
        return manager_app

    @classmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""
        return True

    def print_status(self) -> None:
        """Print the status of the plugin."""
        is_supported = (
            "[bold green]supported[/]"
            if self.is_supported()
            else "[bold red]not supported[/]"
        )

        rich.print(f"{self.name} is {is_supported}.")
