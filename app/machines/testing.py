"""Testing machine."""

from functools import partial
from time import sleep

import typer
from rich.progress import track

from app import utils
from app.config import MachineConfig, UnixEnvironment, WindowsEnvironment
from app.plugins import private_files

app: typer.Typer = typer.Typer(name="test")
private = partial(private_files.setup)
app.command(name="private")(private.func)


@app.callback(invoke_without_command=True)
def setup(cx: typer.Context) -> None:
    """Setup a machine with the provided name."""
    if cx.invoked_subcommand is not None:
        return

    config_files = MachineConfig()
    utils.LOGGER.debug("Config files: %s", config_files.model_dump_json(indent=2))

    if utils.WINDOWS:
        win_env = WindowsEnvironment()
        utils.LOGGER.debug("Environment: %s", win_env.model_dump_json(indent=2))

    if utils.LINUX or utils.MACOS:
        unix_env = UnixEnvironment()
        utils.LOGGER.debug("Environment: %s", unix_env.model_dump_json(indent=2))

    utils.LOGGER.info("Setting up machine...")
    for _ in track(range(15), description="Processing...", transient=True):
        sleep(0.1)

    utils.LOGGER.info("Machine setup completed successfully")
    raise typer.Exit()
