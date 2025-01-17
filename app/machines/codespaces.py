"""Github Codespace machine."""

__all__ = ["Codespace"]

import os

from app import config, env, plugins, utils
from app.machine import MachinePlugin
from app.models import PluginProtocol


class Codespace(MachinePlugin[config.Codespaces, env.Unix]):
    """Github codespaces machine configuration."""

    shell = utils.Shell()

    @property
    def _config(self) -> config.Codespaces:
        return config.Codespaces()

    @property
    def _env(self) -> env.Unix:
        return env.Unix(env_file=self._config.zshenv)

    @property
    def plugins(self) -> list[type[PluginProtocol]]:
        return [
            plugins.Fonts,
            plugins.Git,
            plugins.ZSH,
        ]

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
