"""Testing machine."""

from functools import partial
from pathlib import Path

import typer

from app import config, env, utils
from app.plugins import private_files


class TestingConfig(config.Private):
    """Testing machine configuration files."""

    valid_field: Path = utils.create_temp_file("valid_field")
    invalid_field: int = 0


machine_app = typer.Typer(name="test", help="Testbench.")

private_cmd = partial(
    private_files.setup,
    private_config=TestingConfig(),
    private_dir=utils.create_temp_dir("private"),
)
plugin_app = utils.create_plugin(private_files, private_cmd)
machine_app.add_typer(plugin_app)


@machine_app.command()
def setup() -> None:
    """Test setting up a machine."""
    utils.LOGGER.info("Setting up machine...")
    utils.post_install_tasks += [
        lambda: utils.LOGGER.info("Machine setup completed successfully")
    ]

    config_files = TestingConfig()
    environment = (env.Windows if utils.WINDOWS else env.Unix)()
    utils.LOGGER.debug("Config files: %s", config_files.model_dump_json(indent=2))
    utils.LOGGER.debug("Environment: %s", environment.model_dump_json(indent=2))

    temp_dir = utils.create_temp_dir("private")
    (temp_dir / config_files.valid_field.name).touch()
    private_files.setup(private_dir=temp_dir, private_config=config_files)
