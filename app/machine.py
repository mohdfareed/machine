"""Machine interface for configuring and setting up machines."""

__all__ = ["MachinePlugin"]


from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, TypeVar

import typer

from app import config, env, models, plugin, utils

C = TypeVar("C", bound=config.MachineConfig)
E = TypeVar("E", bound=env.MachineEnv)


class MachinePlugin(plugin.Plugin[C, E], models.MachineProtocol, ABC):
    """Base class for defining a machine with specific plugins."""

    @property
    @abstractmethod
    def _config(self) -> C:
        """The machine's configuration."""

    @property
    @abstractmethod
    def _env(self) -> E:
        """The machine's environment."""

    def __init__(self) -> None:
        if not self.is_supported():
            raise models.MachineException(f"{self.name} is not supported.")
        super().__init__(self._config, self._env)

    @utils.hidden
    def app(self) -> typer.Typer:
        def app_callback() -> None:
            utils.LOGGER.debug(
                "Configuration: %s",
                self.config.model_dump_json(indent=2),
            )
            utils.LOGGER.debug(
                "Environment: %s",
                self.config.model_dump_json(indent=2),
            )

        @wraps(self.setup)
        def setup_wrapper(*args: Any, **kwargs: Any) -> None:
            """Set up the machine."""
            utils.LOGGER.info("Setting up machine...")
            utils.post_install_tasks += [
                lambda: utils.LOGGER.info("Machine setup completed.")
            ]
            self.setup(*args, **kwargs)

        plugins_app = typer.Typer(name="plugins", help="Manage machine plugins.")
        for plugin_instance in self.create_plugins():
            plugins_app.add_typer(plugin_instance.app())

        machine_app = super().app()
        machine_app.callback()(app_callback)
        machine_app.command()(setup_wrapper)
        machine_app.add_typer(plugins_app)
        return machine_app

    def setup(self) -> None:
        """Set up the machine."""
        plugins = self.create_plugins()
        for plugin_instance in plugins:
            plugin_instance.setup()

    @utils.hidden
    def create_plugins(self) -> list[models.PluginProtocol]:
        """Create plugins for the machine."""
        return [
            plugin(
                config=self.config,
                env=self.env,
            )
            for plugin in self.plugins
        ]
