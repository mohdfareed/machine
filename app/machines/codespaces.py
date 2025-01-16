"""Github Codespace machine."""

__all__ = ["Codespace"]

import os
from typing import Any

from app import config, env, plugins, utils
from app.machine import MachinePlugin
from app.plugin import Plugin


class Codespace(MachinePlugin[config.Codespaces, env.Unix]):
    """Github codespaces machine configuration."""

    shell = utils.Shell()

    @property
    def plugins(self) -> list[type[Plugin[Any, Any]]]:
        return [
            plugins.Fonts,
            plugins.Git,
            plugins.ZSH,
        ]

    def __init__(self) -> None:
        configuration = config.Codespaces()
        super().__init__(configuration, env.Unix().load(configuration.zshenv))

    @classmethod
    def is_supported(cls) -> bool:
        return utils.LINUX and os.getenv("CODESPACES") == "true"

    def setup(self) -> None:
        super().setup()
        self.set_shell()

    def set_shell(self, shell: str = "/usr/bin/zsh") -> None:
        """Set the machine's default shell."""
        utils.LOGGER.info("Setting the default shell to: %s", shell)
        self.shell.execute(f'sudo chsh "$(id -un)" --shell "{shell}"')
