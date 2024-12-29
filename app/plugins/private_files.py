"""Private files plugin."""

__all__ = ["Private", "PrivateConfigData"]

from pathlib import Path
from typing import Annotated

import typer

from app import config, models, utils
from app.plugins.plugin import Plugin, SetupFunc

SSH_KEYS_DIRNAME = "keys"
PRIVATE_ENV_FILENAME = "private.sh"

PrivateDirArg = Annotated[
    Path,
    typer.Argument(
        help="The private files directory.",
        callback=utils.validate(utils.is_dir),
    ),
]


class PrivateConfigData(models.ConfigFiles):
    """Private configuration files."""

    config: Path = config.Machine().config / "private"
    private_env: Path = config / PRIVATE_ENV_FILENAME
    ssh_keys: Path = config / SSH_KEYS_DIRNAME


class Private(Plugin[PrivateConfigData, None]):
    """Setup private config files."""

    @property
    def plugin_setup(self) -> SetupFunc:
        return self._setup

    def __init__(self, private_config: PrivateConfigData = PrivateConfigData()) -> None:
        """Initialize the plugin."""
        super().__init__(private_config, None)

    def _setup(self, private_dir: PrivateDirArg) -> None:
        utils.LOGGER.debug("Private directory: %s", private_dir)

        # copy ssh keys
        if self.config.ssh_keys.exists():
            local_ssh_keys = private_dir / SSH_KEYS_DIRNAME
            utils.link(local_ssh_keys, self.config.ssh_keys)
        else:
            utils.LOGGER.warning(
                "Private SSH keys directory does not exist at: %s", self.config.ssh_keys
            )

        # copy private
        if self.config.private_env.exists():
            local_private_env = private_dir / PRIVATE_ENV_FILENAME
            utils.link(local_private_env, self.config.private_env)
        else:
            utils.LOGGER.warning(
                "Private environment keys directory does not exist at: %s",
                self.config.private_env,
            )
