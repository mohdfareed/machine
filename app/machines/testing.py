"""Testing machine."""

from functools import partial

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
def setup() -> None:
    """Test setting up a machine."""

    config_files = config.Machine()
    utils.LOGGER.debug("Config files: %s", config_files.model_dump_json(indent=2))
    environment = env.Environment.os_env()
    utils.LOGGER.debug("Environment: %s", environment.model_dump_json(indent=2))
    utils.LOGGER.info("Setting up machine...")

    private_cmd(typer.prompt("Private directory"))
    git_cmd()

    utils.LOGGER.info("Machine setup completed successfully")
    raise typer.Exit()
