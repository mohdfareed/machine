"""Testing machine."""

from functools import partial
from time import sleep

import typer
from rich.progress import track

from app import config, env, plugins, utils

app = typer.Typer(name="test", help="Testing machine.")

private_cmd = partial(plugins.private_files.setup)
plugin_app = plugins.create(plugins.private_files, private_cmd)
app.add_typer(plugin_app)


@app.command()
def setup(cx: typer.Context) -> None:
    """Test setting up a machine."""
    if cx.invoked_subcommand is not None:
        return

    config_files = config.Machine()
    utils.LOGGER.debug("Config files: %s", config_files.model_dump_json(indent=2))

    if utils.WINDOWS:
        win_env = env.Windows()
        utils.LOGGER.debug("Environment: %s", win_env.model_dump_json(indent=2))

    if utils.LINUX or utils.MACOS:
        unix_env = env.Unix()
        utils.LOGGER.debug("Environment: %s", unix_env.model_dump_json(indent=2))

    utils.LOGGER.info("Setting up machine...")
    for _ in track(range(15), description="Processing...", transient=True):
        sleep(0.1)

    utils.LOGGER.info("Machine setup completed successfully")
    raise typer.Exit()
