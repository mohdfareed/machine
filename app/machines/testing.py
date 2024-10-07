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


class TestingEnvironment(env.Environment):
    """Testing machine configuration files."""

    MACHINE: Path = utils.create_temp_dir("machine")
    GITCONFIG: Path = utils.create_temp_file(".gitconfig")
    GITIGNORE: Path = utils.create_temp_file(".gitignore")


class TestingPrivateConfig(config.Private):
    """Testing private configuration files."""

    valid_field: Path = utils.create_temp_file("private_env_field")
    invalid_field: int = 0


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
        (private_dir / TestingPrivateConfig().valid_field.name).touch()
        private_cmd(private_dir, TestingPrivateConfig)
    git_cmd(environment=TestingEnvironment())

    utils.LOGGER.info("Machine setup completed successfully")
    raise typer.Exit()
