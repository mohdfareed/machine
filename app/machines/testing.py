"""Testing machine."""

from functools import partial
from pathlib import Path
from typing import Annotated, Optional

import typer

from app import config, env, plugins, utils

app = typer.Typer(name="test", help="Testing machine.")

private_cmd = partial(plugins.private_files.setup)
plugin_app = plugins.create(plugins.private_files, private_cmd)
app.add_typer(plugin_app)

git_cmd = partial(plugins.git.setup)
plugin_app = plugins.create(plugins.git, git_cmd)
app.add_typer(plugin_app)


@app.command()
def setup(
    private_dir: Annotated[
        Optional[Path],
        typer.Argument(
            help="The private files directory.",
            callback=utils.validate(utils.is_optional, utils.is_dir),
        ),
    ] = None,
) -> None:
    """Test setting up a machine."""
    utils.LOGGER.info("Setting up machine...")

    config_files = config.Machine()
    utils.LOGGER.debug("Config files: %s", config_files.model_dump_json(indent=2))
    environment = env.Environment.os_env().load()
    utils.LOGGER.debug("Environment: %s", environment.model_dump_json(indent=2))

    if private_dir:
        private_cmd(private_dir)
    git_cmd()

    utils.LOGGER.info("Machine setup completed successfully")
    raise typer.Exit()
