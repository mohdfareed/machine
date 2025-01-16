"""Machine interface for configuring and setting up machines."""

__all__ = ["MachinePlugin"]


from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, TypeVar

import typer

from app import config, env, utils
from app.models import (
    ConfigProtocol,
    EnvironmentProtocol,
    MachineException,
    MachineProtocol,
    PluginProtocol,
)
from app.plugin import Plugin

C = TypeVar("C", bound=ConfigProtocol)
E = TypeVar("E", bound=EnvironmentProtocol)


class MachinePlugin(
    Plugin[C, E], MachineProtocol, ABC
):  # pylint: disable=too-many-ancestors
    """Base class for defining a machine with specific plugins."""

    @property
    @abstractmethod
    def plugins(self) -> list[type[PluginProtocol]]:
        """List of plugins to be registered to the machine."""

    @abstractmethod
    def __init__(self) -> None:
        self.config: C
        self.env: E

        if not self.is_supported():
            raise MachineException(f"{self.name} is not supported.")
        super().__init__(self.config, self.env)

    @classmethod
    def machine_app(cls: "type[MachineProtocol]") -> typer.Typer:
        """Create a Typer app for the machine."""
        instance = cls()

        def app_callback() -> None:
            if isinstance(instance.config, config.MachineConfig):
                utils.LOGGER.debug(
                    "Configuration: %s", instance.config.model_dump_json(indent=2)
                )
            if isinstance(instance.env, env.MachineEnv):
                utils.LOGGER.debug(
                    "Environment: %s", instance.env.model_dump_json(indent=2)
                )

        @wraps(instance.setup)
        def setup_wrapper(*args: Any, **kwargs: Any) -> None:
            utils.LOGGER.info("Setting up machine...")
            utils.post_install_tasks += [
                lambda: utils.LOGGER.info("Machine setup completed successfully")
            ]
            instance.setup(*args, **kwargs)

        plugins_app = typer.Typer(name="plugins", help="Manage machine plugins.")
        for plugin in MachinePlugin.create_plugins(instance):
            plugins_app.add_typer(plugin.app(plugin))

        machine_app = super().app(instance)
        machine_app.callback()(app_callback)
        machine_app.command(help="Set up the machine.")(setup_wrapper)
        machine_app.add_typer(plugins_app)
        return machine_app

    def setup(self) -> None:
        """Machine setup."""
        plugins = MachinePlugin.create_plugins(self)
        for plugin in plugins:
            plugin.setup()

    @staticmethod
    def create_plugins(instance: "MachineProtocol") -> list[PluginProtocol]:
        """Create plugins for the machine."""
        return [
            plugin(configuration=instance.config, environment=instance.env)
            for plugin in instance.plugins
        ]
