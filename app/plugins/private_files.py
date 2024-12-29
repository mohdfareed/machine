"""Private files plugin."""

__all__ = ["Private", "PrivateConfigData"]

from pathlib import Path
from typing import Annotated

import typer

from app import config, utils
from app.plugins.plugin import Configuration, Plugin, SetupFunc

SSH_KEYS_DIRNAME = "keys"
PRIVATE_ENV_FILENAME = "private.sh"

PrivateDirArg = Annotated[
    Path,
    typer.Argument(
        help="The private files directory.",
        callback=utils.validate(utils.is_dir),
    ),
]


class PrivateConfigData(Configuration):
    """Private configuration files."""

    config: Path = config.Machine().config / "private"
    private_env: Path = config / PRIVATE_ENV_FILENAME
    ssh_keys: Path = config / SSH_KEYS_DIRNAME


class Private(Plugin[PrivateConfigData, None]):
    """Setup private config files."""

    @property
    def plugin_setup(self) -> SetupFunc:
        return self._setup

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__(PrivateConfigData(), None)

    def _setup(self, private_dir: PrivateDirArg) -> None:
        utils.LOGGER.debug("Private directory: %s", private_dir)

        # copy ssh keys
        if self.config.ssh_keys.exists():
            local_ssh_keys = private_dir / SSH_KEYS_DIRNAME
            utils.link(self.config.ssh_keys, local_ssh_keys)
        else:
            utils.LOGGER.warning(
                "Private SSH keys directory does not exist at: %s", self.config.ssh_keys
            )

        # copy private
        if self.config.private_env.exists():
            local_private_env = private_dir / PRIVATE_ENV_FILENAME
            utils.link(self.config.private_env, local_private_env)
        else:
            utils.LOGGER.warning(
                "Private environment keys directory does not exist at: %s",
                self.config.private_env,
            )
