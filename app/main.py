"""Main module for the Typer Machine Setup CLI."""

__all__ = ["app"]

import os
import platform
import time
from pathlib import Path
from typing import Annotated, Optional

import typer
import typer.completion

from app import APP_NAME, __version__, env, machine, utils
from app.utils.logging import log_file_path

COMPLETION_APP = "completion"

app = typer.Typer(
    name=APP_NAME,
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)

# completion app
app_completion = typer.Typer(
    help="Generate and install completion scripts.", add_completion=True
)
app.add_typer(app_completion, name=COMPLETION_APP)

# register machines
for available_machine in machine.machines():
    app.add_typer(available_machine.app())


@app.callback()
def main(
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
    utils.add_post_setup_task(install)


@app_completion.command()
def install() -> None:
    """Install shell completions."""
    command = f"poetry run {APP_NAME} {COMPLETION_APP}"
    time.sleep(5)

    if not utils.Platform.UNIX:
        utils.LOGGER.error("Unsupported platform for auto shell completions.")
        code, _ = utils.Shell().execute(f"{command} install-completion")
        raise typer.Exit(code)

    if not os.environ.get("MACHINE"):
        utils.LOGGER.error("MACHINE environment variable is not set.")
        code, _ = utils.Shell().execute(f"{command} install-completion")
        raise typer.Exit(code)

    if not env.Unix().COMPLETIONS_PATH.exists():
        env.Unix().COMPLETIONS_PATH.mkdir(parents=True, exist_ok=True)

    utils.LOGGER.info("Generating completions...")
    temp_file = utils.create_temp_file()
    os.chdir(os.environ["MACHINE"])
    utils.Shell().execute(f"{command} show-completion > '{temp_file}'")

    comp_path = env.Unix().COMPLETIONS_PATH / APP_NAME
    utils.LOGGER.debug("Installing completions at: %s", comp_path)
    temp_file.rename(comp_path)
    utils.LOGGER.info("Shell completions installed successfully.")


@app_completion.command(hidden=True)
def show_completion(ctx: typer.Context, shell: Optional[str] = None) -> None:
    """Wrapper around built-in Typer completion command."""
    shell = shell or Path(utils.OS_EXECUTABLE.value).name
    typer.completion.show_callback(ctx, None, shell)  # type: ignore


@app_completion.command(hidden=True)
def install_completion(ctx: typer.Context, shell: Optional[str] = None) -> None:
    """Wrapper around built-in Typer completion command."""
    shell = shell or Path(utils.OS_EXECUTABLE.value).name
    typer.completion.install_callback(ctx, None, shell)  # type: ignore
