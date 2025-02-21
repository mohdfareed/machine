"""Machine interface for configuring and setting up machines."""

__all__ = ["MachinePlugin", "machines"]


from abc import ABC, abstractmethod
from inspect import isabstract
from typing import Any, Optional, TypeVar

import typer
from typing_extensions import override

from app import config, env, models, pkg_manager, plugin, utils

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
        super().__init__(self._config, self._env)

    @utils.hidden
    @override
    def app(self) -> typer.Typer:
        def app_callback() -> None:
            utils.LOGGER.debug(
                "Configuration: %s",
                self.config.model_dump_json(indent=2),
            )
            utils.LOGGER.debug(
                "Environment: %s",
                self.env.model_dump_json(indent=2),
            )

        plugins_app = typer.Typer(
            name="plugins", help="Manage machine plugins."
        )
        for plugin_instance in self.create_plugins():
            plugins_app.add_typer(plugin_instance.app())

        managers_app = typer.Typer(name="pkg", help="Package managers.")
        for manager in self.create_pkg_managers():
            managers_app.add_typer(manager.app())

        machine_app = super().app()
        machine_app.callback()(app_callback)
        machine_app.add_typer(plugins_app)
        machine_app.add_typer(managers_app)
        return machine_app

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

    @staticmethod
    def create_pkg_managers() -> list[models.PkgManagerProtocol]:
        """Create package managers for the machine."""
        return [
            manager()  # type: ignore
            for manager in pkg_manager.PkgManagerPlugin.__subclasses__()
            if not isabstract(manager) and manager.is_supported()
        ]

    @utils.hidden
    def execute_setup(
        self, setup_tasks: Optional[list[utils.SetupTask]] = None
    ) -> None:
        """Execute the machine setup."""
        utils.LOGGER.info("Setting up machine: %s", self.name)
        total = len(self.plugins) + len(setup_tasks or [])
        task_id = utils.progress.add_task(
            f"[green]Setting up {self.name}...", total=total
        )

        plugins = self.create_plugins()
        for plugin_instance in plugins:
            plugin_instance.setup()
            utils.progress.update(task_id, advance=1)

        for setup_task in setup_tasks or []:
            setup_task()
            utils.progress.update(task_id, advance=1)

        utils.post_setup()
        utils.progress.update(task_id, advance=1)

        utils.progress.remove_task(task_id)
        utils.LOGGER.info("Machine setup complete.")

    # Disconnect inherited plugin setup method

    @abstractmethod
    def setup(self) -> None: ...

    @utils.hidden
    def _setup(self) -> None: ...


def machines() -> "list[MachinePlugin[Any, Any]]":
    """List all machine plugins."""
    import app.machines as _  # pylint: disable=import-outside-toplevel

    machine: MachinePlugin[Any, Any]
    available_machines: list[MachinePlugin[Any, Any]] = []

    for machine in MachinePlugin.__subclasses__():  # type: ignore
        if not machine.is_supported() or isabstract(machine):
            continue
        available_machines.append(machine())  # type: ignore
    return available_machines
