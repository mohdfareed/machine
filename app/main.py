"""Main module for the Typer Machine Setup CLI."""

import os
import platform
from typing import Annotated

import typer

from app import APP_NAME, __version__, env, machines, utils
from app.pkg_manager import pkg_managers_app
from app.utils.logging import log_file_path

app = typer.Typer(
    name=APP_NAME,
    context_settings={"help_option_names": ["-h", "--help"]},
    result_callback=utils.post_installation,
)

# register machines and package managers
for machine_app in machines.apps:
    app.add_typer(machine_app)
app.add_typer(pkg_managers_app())


@app.callback()
def main(
    ctx: typer.Context,
    debug_mode: Annotated[
        bool,
        typer.Option("--debug", "-d", help="Log debug messages to the console."),
    ] = False,
) -> None:
    """Machine setup CLI."""

    # initialize logging
    utils.setup_logging(debug_mode)
    platform_info = f"[blue]{platform.platform().replace('-', '[black]|[/]')}[/]"

    # debug information
    utils.LOGGER.debug("Machine version: %s", __version__)
    utils.LOGGER.debug("Python version: %s", platform.python_version())
    utils.LOGGER.debug("Platform: %s", platform_info)
    utils.LOGGER.debug("Debug mode: %s", debug_mode)
    utils.LOGGER.debug("Log file: %s", log_file_path)

    # setup post installation tasks
    if ctx.invoked_subcommand != completions.__name__:
        utils.post_install_tasks = [completions]


@app.command()
def completions() -> None:
    """Install shell completions."""

    if not utils.UNIX:
        utils.LOGGER.error("Unsupported platform for shell completions.")
        raise typer.Abort

    if not os.environ.get("MACHINE"):
        utils.LOGGER.error("MACHINE environment variable is not set.")
        raise typer.Abort

    if not env.Unix().COMPLETIONS_PATH.exists():
        env.Unix().COMPLETIONS_PATH.mkdir(parents=True, exist_ok=True)

    utils.LOGGER.info("Generating completions...")
    temp_file = utils.create_temp_file()
    os.chdir(os.environ["MACHINE"])
    utils.Shell().execute(f"poetry run {APP_NAME} --show-completion > '{temp_file}'")

    comp_path = env.Unix().COMPLETIONS_PATH / APP_NAME
    utils.LOGGER.debug("Installing completions at: %s", comp_path)
    temp_file.rename(comp_path)
    utils.LOGGER.info("Shell completions installed successfully.")
