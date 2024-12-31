"""Machine interface for configuring and setting up machines."""

__all__ = ["Machine"]


from abc import abstractmethod
from typing import Any, Generic, List

import typer

from app import utils
from app.models import ConfigFiles, Environment, MachineException
from app.plugins import app as plugins_app
from app.plugins.plugin import C, E, Plugin, SetupFunc


class Machine(Plugin[C, E], Generic[C, E]):
    """Base class for defining a machine with specific plugins."""

    @property
    def plugin_setup(self) -> SetupFunc:
        """Plugin-specific setup steps."""

        def setup_wrapper() -> None:
            utils.LOGGER.info("Setting up machine...")
            utils.post_install_tasks += [
                lambda: utils.LOGGER.info("Machine setup completed successfully")
            ]
            self.machine_setup()

        return setup_wrapper

    @property
    @abstractmethod
    def machine_setup(self) -> SetupFunc:
        """Machine-specific setup steps."""

    @property
    def plugins(self) -> List[Plugin[Any, Any]]:
        """List of plugins to be registered to the machine."""
        return []

    def __init__(self, config: C, env: E) -> None:
        if not self.is_supported():
            raise MachineException(f"{self.name} is not supported.")
        super().__init__(config, env)

    def app_callback(self) -> None:
        """Callback for the Typer app."""
        if isinstance(self.config, ConfigFiles):
            utils.LOGGER.debug(
                "Configuration: %s", self.config.model_dump_json(indent=2)
            )
        if isinstance(self.env, Environment):
            utils.LOGGER.debug("Environment: %s", self.env.model_dump_json(indent=2))

    def app(self) -> typer.Typer:
        machine_app = super().app()
        machine_app.callback()(self.app_callback)
        machine_app.add_typer(plugins_app(self.plugins))
        return machine_app

    @classmethod
    @abstractmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""
