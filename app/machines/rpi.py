"""Raspberry Pi machine."""

__all__ = ["RPi"]

from typing import Any

from app import config, env, plugins, utils
from app.machine import Machine
from app.plugin import Plugin
from app.plugins.pkg_managers.linux import SnapStore

VSCODE_TUNNELS_NAME = "rpi"

Environment = env.Unix if utils.UNIX else env.Windows


class RPi(Machine[config.RPi, env.Unix]):
    """Raspberry Pi machine."""

    shell = utils.Shell()

    @property
    def plugins(self) -> list[type[Plugin[Any, Any]]]:
        return [
            plugins.Private,
            plugins.Fonts,
            plugins.Git,
            plugins.ZSH,
            plugins.SSH,
            plugins.NeoVim,
            plugins.Btop,
            plugins.PowerShell,
            plugins.VSCode,
            plugins.Tailscale,
            plugins.Docker,
            plugins.Python,
        ]

    def __init__(self) -> None:
        configuration = config.RPi()
        super().__init__(configuration, env.Unix().load(configuration.zshenv))

    @classmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""
        return True

    def setup(self) -> None:
        super().setup()
        plugins.SSH(self.config, self.env).generate_key_pair("personal")
        plugins.SSH(self.config, self.env).setup_server()
        plugins.VSCode(self.config, self.env).setup_tunnels(VSCODE_TUNNELS_NAME)
        SnapStore().install_classic("go dotnet-sdk")
        self.post_setup()

    def post_setup(self) -> None:
        """Post-setup tasks."""
        self.shell.execute(
            "sudo loginctl enable-linger $USER", throws=False
        )  # code server
        self.shell.execute(
            "sudo chsh -s $(which zsh)", throws=False
        )  # change default shell
        self.shell.execute(
            "sudo touch $HOME/.hushlogin", throws=False
        )  # remove login message
        self.shell.execute(
            "sudo mkdir -p $HOME/.config", throws=False
        )  # create config directory
