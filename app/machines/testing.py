"""Testing machine."""

from functools import partial
from pathlib import Path

import typer

from app import config, env, plugins, utils


class TestingEnvironment(env.Windows, env.Unix):
    """Testing machine configuration files."""

    MACHINE: Path = utils.create_temp_dir("machine")
    GITCONFIG: Path = MACHINE / "gitconfig"
    GITIGNORE: Path = MACHINE / "gitignore"


class TestingConfig(config.Private):
    """Testing machine configuration files."""

    valid_field: Path = utils.create_temp_file("valid_field")
    invalid_field: int = 0


app = typer.Typer(name="test", help="Testing machine.")

private_cmd = partial(plugins.private_files.setup, private_config=TestingConfig())
plugin_app = plugins.create(plugins.private_files, private_cmd)
app.add_typer(plugin_app)

git_cmd = partial(
    plugins.git.setup,
    gitconfig=utils.create_temp_file("gitconfig"),
    gitignore=utils.create_temp_file("gitignore"),
    environment=TestingEnvironment(),
)
plugin_app = plugins.create(plugins.git, git_cmd)
app.add_typer(plugin_app)


@app.command()
def setup(
    private_dir: plugins.private_files.PrivateDirArg = utils.create_temp_dir("private"),
) -> None:
    """Test setting up a machine."""
    utils.LOGGER.info("Setting up machine...")

    config_files = TestingConfig()
    environment = TestingEnvironment()
    utils.LOGGER.debug("Config files: %s", config_files.model_dump_json(indent=2))
    utils.LOGGER.debug("Environment: %s", environment.model_dump_json(indent=2))

    (private_dir / config_files.valid_field.name).touch()
    private_cmd(private_dir=private_dir)
    git_cmd()

    utils.LOGGER.info("Machine setup completed successfully")
    raise typer.Exit()
