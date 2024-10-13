"""Main module for the Typer Machine Setup CLI."""

import platform
from typing import Annotated

import typer

from app import APP_NAME, __version__, env, machines, pkg_managers, plugins, utils
from app.utils.logging import log_file_path

app = typer.Typer(
    name=APP_NAME,
    context_settings={"help_option_names": ["-h", "--help"]},
    result_callback=utils.post_installation,
    add_completion=False,
)

# register machines, plugins, and package managers
app.add_typer(machines.app)
app.add_typer(plugins.app)
app.add_typer(pkg_managers.app)


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


def completions() -> None:
    """Install shell completions."""
    temp_file = utils.create_temp_file()
    temp_file.parent.mkdir(parents=True, exist_ok=True)

    utils.Shell().execute(f"poetry run {APP_NAME} --show-completion > '{temp_file}'")
    temp_file.rename(env.Unix().COMPLETIONS_PATH / APP_NAME)


if utils.UNIX:
    app.command()(completions)
