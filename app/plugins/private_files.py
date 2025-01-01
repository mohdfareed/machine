"""Private files plugin."""

__all__ = ["Private"]

from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from app import utils
from app.plugins.plugin import Plugin, SetupFunc

# typechecking imports
if TYPE_CHECKING:
    from app import config

PrivateDirArg = Annotated[
    Path,
    typer.Argument(
        help="The private files directory.",
        callback=utils.validate(utils.is_dir),
    ),
]


class Private(Plugin["config.Private", None]):
    """Setup private config files."""

    @property
    def plugin_setup(self) -> SetupFunc:
        return self._setup

    def __init__(self, private_config: "config.Private") -> None:
        """Initialize the plugin."""
        super().__init__(private_config, None)

    def _setup(self, private_dir: PrivateDirArg) -> None:
        utils.LOGGER.debug("Private directory: %s", private_dir)

        # copy ssh keys
        local_ssh_keys = private_dir / self.config.ssh_keys.name
        if local_ssh_keys.exists():
            utils.link(local_ssh_keys, self.config.ssh_keys)
            utils.LOGGER.info("Loaded private data: %s", local_ssh_keys)
        else:
            utils.LOGGER.warning(
                "Private SSH keys directory does not exist at: %s", local_ssh_keys
            )

        # copy private
        local_private_env = private_dir / self.config.private_env.name
        if local_private_env.exists():
            utils.link(local_private_env, self.config.private_env)
            utils.LOGGER.info("Loaded private data%s", local_private_env)
        else:
            utils.LOGGER.warning(
                "Private environment file does not exist at: %s",
                self.config.private_env,
            )
