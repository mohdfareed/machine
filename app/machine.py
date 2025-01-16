"""Machine interface for configuring and setting up machines."""

__all__ = ["MachinePlugin"]


from abc import abstractmethod
from functools import wraps
from typing import Any, List, TypeVar

import typer

from app import config, env, main, utils
from app.models import (
    ConfigProtocol,
    EnvironmentProtocol,
    MachineException,
    MachineProtocol,
)
from app.plugin import Plugin

C = TypeVar("C", bound=ConfigProtocol)
E = TypeVar("E", bound=EnvironmentProtocol)


class MachinePlugin(Plugin[C, E], MachineProtocol):
    """Base class for defining a machine with specific plugins."""

    @property
    def machine_setup(self) -> Any:
        """Machine setup decorator."""

        @wraps(self.setup)
        def setup_wrapper(*args: Any, **kwargs: Any) -> None:
            """Set up the machine."""
            utils.LOGGER.info("Setting up machine...")
            main.completions()
            utils.post_install_tasks += [
                lambda: utils.LOGGER.info("Machine setup completed successfully")
            ]
            self.setup(*args, **kwargs)

        return setup_wrapper

    @property
    @abstractmethod
    def plugins(self) -> List[type[Plugin[Any, Any]]]:
        """List of plugins to be registered to the machine."""

    def __init__(self, configuration: C, environment: E) -> None:
        if not self.is_supported():
            raise MachineException(f"{self.name} is not supported.")
        super().__init__(configuration, environment)

    @classmethod
    def machine_app(cls, instance: "MachinePlugin[Any, Any]") -> typer.Typer:
        """Create a Typer app for the machine."""

        def app_callback() -> None:
            if isinstance(instance.config, config.MachineConfig):
                utils.LOGGER.debug(
                    "Configuration: %s", instance.config.model_dump_json(indent=2)
                )
            if isinstance(instance.env, env.MachineEnv):
                utils.LOGGER.debug(
                    "Environment: %s", instance.env.model_dump_json(indent=2)
                )

        plugins_app = typer.Typer(name="plugins", help="Manage machine plugins.")
        for plugin in instance._create_plugins():  # pylint: disable=protected-access
            plugins_app.add_typer(plugin.app(plugin))

        machine_app = super().app(instance)
        machine_app.callback()(app_callback)
        machine_app.command(help="Set up the machine.")(instance.machine_setup)
        machine_app.add_typer(plugins_app)
        return machine_app

    def setup(self) -> None:
        """Machine setup."""
        plugins = self._create_plugins()
        for plugin in plugins:
            plugin.setup()

    def _create_plugins(self) -> List[Plugin[Any, Any]]:
        return [plugin(self.config, self.env) for plugin in self.plugins]


def machines_apps() -> list[typer.Typer]:
    """List of supported machines apps."""
    machines: list[typer.Typer] = []
    for machine in MachinePlugin.__subclasses__():
        if not machine.is_supported() or isabstract(machine):
            continue
        machines.append(machine.machine_app(machine()))
    return machines
