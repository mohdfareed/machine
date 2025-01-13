"""Machine interface for configuring and setting up machines."""

__all__ = ["Machine"]


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


class Machine(Plugin[C, E], MachineProtocol):
    """Base class for defining a machine with specific plugins."""

    @property
    def machine_setup(self) -> Any:
        """Machine setup decorator."""

        @wraps(self.setup)
        def setup_wrapper(*args: Any, **kwargs: Any) -> None:
            utils.LOGGER.info("Setting up machine...")
            main.completions()
            utils.post_install_tasks += [
                lambda: utils.LOGGER.info("Machine setup completed successfully")
            ]
            self.setup(*args, **kwargs)

        return setup_wrapper

    @property
    @abstractmethod
    def plugins(self) -> List[Plugin[Any, Any]]:
        """List of plugins to be registered to the machine."""

    def __init__(self, configuration: C, environment: E) -> None:
        if not self.is_supported():
            raise MachineException(f"{self.name} is not supported.")
        super().__init__(configuration, environment)

    @classmethod
    def machine_app(cls, instance: "Machine[Any, Any]") -> typer.Typer:
        """Create a Typer app for the machine."""

        def app_callback() -> None:
            if isinstance(instance.config, config.Machine):
                utils.LOGGER.debug(
                    "Configuration: %s", instance.config.model_dump_json(indent=2)
                )
            if isinstance(instance.env, env.Machine):
                utils.LOGGER.debug(
                    "Environment: %s", instance.env.model_dump_json(indent=2)
                )

        machine_app = super().app(instance)
        machine_app.callback()(app_callback)
        machine_app.command()(instance.setup)

        for plugin in instance.plugins:
            machine_app.add_typer(plugin.app(plugin))
        return machine_app

    def setup(self) -> None:
        """Set up the machine."""
        for plugin in self.plugins:
            plugin.setup()
