"""Main module for the Typer Machine Setup CLI."""

import platform
from typing import Annotated, Any, Callable

import typer

from app import APP_NAME, __version__, machines, utils
from app.plugins.package_managers import PackageManager
from app.utils.logging import log_file_path

post_install_tasks: list[Callable[[], None]] = []
"""Post installation tasks."""


def _run_post_install_tasks(*_: Any, **__: Any) -> None:
    for task in post_install_tasks:
        task()


app = typer.Typer(
    name=APP_NAME,
    context_settings={"help_option_names": ["-h", "--help"]},
    result_callback=_run_post_install_tasks,
)

# register machine apps
machines_app = typer.Typer(name="machine", help="Machines setup.")
machines_app.add_typer(machines.testing.machine_app)
app.add_typer(machines_app)

# register package manager apps
for pkg_manager in PackageManager.available_managers():
    app.add_typer(pkg_manager.app())


@app.callback()
def main(
    debug_mode: Annotated[
        bool,
        typer.Option("--debug", "-d", help="Log debug messages to the console."),
    ] = False,
) -> None:
    """Machine setup CLI."""

    # initialize logging
    utils.init_logging(debug_mode)

    # debug information
    utils.LOGGER.debug("Machine version: %s", __version__)
    utils.LOGGER.debug("Python version: %s", platform.python_version())
    utils.LOGGER.debug("Debug mode: %s", debug_mode)
    utils.LOGGER.debug("Log file: %s", log_file_path)
    utils.LOGGER.debug("Platform: [blue]%s[/]", utils.PLATFORM)
    utils.LOGGER.debug("ARM: %s", utils.ARM)
