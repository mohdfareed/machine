"""Testing machine."""

from time import sleep

import typer
from rich.progress import track

from app import utils
from app.config import MachineConfig, UnixEnvironment, WindowsEnvironment

# from app.plugins import private_files

app: typer.Typer = typer.Typer(name="test")

config_files = MachineConfig()
win_env = WindowsEnvironment()
unix_env = UnixEnvironment()


@app.callback(invoke_without_command=True)
def setup(cx: typer.Context) -> None:
    """Setup a machine with the provided name."""
    if cx.invoked_subcommand is not None:
        return

    utils.LOGGER.debug("Config files: %s", config_files.model_dump_json(indent=2))

    if utils.WINDOWS:
        utils.LOGGER.debug("Environment: %s", win_env.model_dump_json(indent=2))
    else:
        utils.LOGGER.debug("Environment: %s", unix_env.model_dump_json(indent=2))

    utils.LOGGER.info("Setting up machine...")
    for _ in track(range(15), description="Processing...", transient=True):
        sleep(0.1)

    utils.LOGGER.info("Machine setup completed successfully")
    raise typer.Exit()


# @app.command()
# def private() -> None:
#     """Setup private files on a machine."""
#     private_files.setup()
#     raise typer.Exit()
