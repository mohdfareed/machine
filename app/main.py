"""Main module for the Typer Machine Setup CLI."""

import platform
from typing import Annotated

import typer

from app import APP_NAME, __version__, env, machines, utils
from app.plugins import pkg_managers
from app.utils.logging import log_file_path

app = typer.Typer(
    name=APP_NAME,
    context_settings={"help_option_names": ["-h", "--help"]},
    result_callback=utils.post_installation,
)

# register machines, and package managers
app.add_typer(machines.app)
app.add_typer(pkg_managers.app())


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
    platform_info = f"[blue]{platform.platform().replace('-', '[black]|[/]')}[/]"

    # debug information
    utils.LOGGER.debug("Machine version: %s", __version__)
    utils.LOGGER.debug("Python version: %s", platform.python_version())
    utils.LOGGER.debug("Platform: %s", platform_info)
    utils.LOGGER.debug("Debug mode: %s", debug_mode)
    utils.LOGGER.debug("Log file: %s", log_file_path)

    # TODO: report machine environment and configuration
    # utils.LOGGER.debug("Environment: %s", env.MachineEnv)
    # utils.LOGGER.debug("Configuration: %s", config.MachineConfig)


@app.command()
def completions() -> None:
    """Install shell completions."""

    if not utils.UNIX:
        utils.LOGGER.error("Unsupported platform for shell completions.")
        raise typer.Abort

    utils.LOGGER.debug("Generating completions...")
    temp_file = utils.create_temp_file()
    utils.Shell().execute(f"poetry run {APP_NAME} --show-completion > '{temp_file}'")

    comp_path = env.Unix().COMPLETIONS_PATH / APP_NAME
    utils.LOGGER.debug("Installing completions at: %s", comp_path)
    temp_file.rename(comp_path)
    utils.LOGGER.info("Shell completions installed successfully.")
