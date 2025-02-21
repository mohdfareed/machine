"""Private files plugin."""

__all__ = ["Private"]

from pathlib import Path
from typing import Annotated, Any, Optional

import typer

from app import config, utils
from app.plugin import Plugin

PrivateDirArg = Annotated[
    Optional[Path],
    typer.Argument(help="The private files directory."),
]


class Private(Plugin[config.Private, Any]):
    """Setup private config files."""

    @classmethod
    def is_supported(cls) -> bool:
        return True

    def ssh_keys(self, private_dir: PrivateDirArg) -> None:
        """Set up private SSH keys."""
        if not (private_dir := self.startup(private_dir)):
            return

        # copy ssh keys
        local_ssh_keys = private_dir / self.config.ssh_keys.name
        if local_ssh_keys.exists():
            utils.link(local_ssh_keys, self.config.ssh_keys)
            utils.LOGGER.info("Loaded private data: %s", local_ssh_keys)
        else:
            utils.LOGGER.warning(
                "Private SSH keys directory does not exist at: %s",
                local_ssh_keys,
            )

    def env_file(self, private_dir: PrivateDirArg) -> None:
        """Set up private environment variables."""
        if not (private_dir := self.startup(private_dir)):
            return

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

    @staticmethod
    def startup(private_dir: PrivateDirArg) -> Optional[Path]:
        """Startup the plugin."""
        if not private_dir:
            utils.LOGGER.warning("Private directory not provided.")
            return None
        utils.LOGGER.debug("Private directory: %s", private_dir)
        return private_dir

    @utils.hidden
    def _setup(self) -> None: ...
