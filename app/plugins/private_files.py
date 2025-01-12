"""Private files plugin."""

__all__ = ["Private"]

from pathlib import Path
from typing import Annotated, Optional

import typer

from app import config, utils
from app.plugins.plugin import Plugin

PrivateDirArg = Annotated[
    Optional[Path],
    typer.Argument(help="The private files directory."),
]


class Private(Plugin["config.Private", None]):
    """Setup private config files."""

    def __init__(self, private_config: "config.Private") -> None:
        """Initialize the plugin."""
        super().__init__(private_config, None)

    @classmethod
    def is_supported(cls) -> bool:
        return True

    def setup(self, private_dir: PrivateDirArg = None) -> None:
        """Set up private files."""
        if not private_dir:
            utils.LOGGER.warning("Private directory not provided.")
            return
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
