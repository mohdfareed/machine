"""macOS machine."""

__all__ = ["MacOS"]

from pathlib import Path
from typing import Any

import typer

from app import config, env, plugins, utils
from app.plugins import pkg_managers
from app.plugins.plugin import Plugin, SetupFunc
from app.plugins.private_files import PrivateDirArg

from .machine import Machine

PAM_SUDO_PATH = Path("/") / "etc" / "pam.d" / "sudo_local"
PAM_SUDO_CONTENT = """
auth       sufficient     pam_tid.so
""".strip()
VSCODE_TUNNELS_NAME = "macbook"


class MacOS(Machine[config.MacOS, env.MacOS]):
    """macOS machine configuration."""

    @property
    def plugins(self) -> list[Plugin[Any, Any]]:
        machine_plugins: list[Plugin[Any, Any]] = [
            plugins.Fonts(),
            plugins.Git(self.config, self.env),
            plugins.Private(self.config),
            plugins.Shell(self.config, self.env),
            plugins.SSH(self.config, self.env),
            plugins.Btop(),
            plugins.NeoVim(self.config, self.env),
            plugins.PowerShell(self.config, self.env),
            plugins.Tailscale(),
            plugins.Docker(),
            plugins.Node(),
            plugins.Python(self.env),
            plugins.VSCode(self.config, self.env),
        ]
        return machine_plugins

    @property
    def machine_setup(self) -> SetupFunc:
        return self._setup

    def __init__(self) -> None:
        super().__init__(config.MacOS(), env.MacOS())

    def app(self) -> typer.Typer:
        machine_app = super().app()
        machine_app.command()(self.system_preferences)
        machine_app.command()(self.enable_touch_id)
        machine_app.command()(self.accept_xcode_license)
        return machine_app

    @classmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""
        return utils.MACOS

    def _setup(self, private_dir: PrivateDirArg) -> None:

        for plugin in self.plugins:
            if isinstance(plugin, plugins.Private):
                plugin.plugin_setup(private_dir=private_dir)
                continue
            if isinstance(plugin, plugins.VSCode):
                plugin.setup_tunnels(VSCODE_TUNNELS_NAME)
            if isinstance(plugin, plugins.SSH):
                plugin.setup_server()
            if isinstance(plugin, plugins.Shell):
                plugin.plugin_setup(machine_id=self.config.machine_id)
                continue
            plugin.plugin_setup()

        self.setup_brew()
        self.system_preferences()
        self.enable_touch_id()

    def setup_brew(self) -> None:
        """Setup Homebrew and install packages."""
        brew = pkg_managers.Brew()
        brew.install_brewfile(self.config.brewfile)
        brew.install("go")
        brew.install("dotnet-sdk", cask=True)
        brew.install("godot-mono", cask=True)

    def system_preferences(self) -> None:
        """Open macOS System Preferences."""
        utils.LOGGER.info("Opening System Preferences...")
        self.shell.execute(f". {self.config.system_preferences}")

    def enable_touch_id(self) -> None:
        """Enable Touch ID for sudo on macOS."""
        utils.LOGGER.info("Enabling Touch ID for sudo...")
        if not PAM_SUDO_PATH.exists():
            PAM_SUDO_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.shell.execute(f"sudo touch {PAM_SUDO_PATH}")

        pam_sudo_contents = PAM_SUDO_PATH.read_text()
        if PAM_SUDO_CONTENT in pam_sudo_contents:
            utils.LOGGER.info("Touch ID for sudo already enabled.")
            return

        self.shell.execute(
            f"echo '{PAM_SUDO_CONTENT}' | sudo tee {PAM_SUDO_PATH} > /dev/null"
        )
        utils.LOGGER.info("Touch ID for sudo enabled.")

    def accept_xcode_license(self) -> None:
        """Accept the Xcode license."""
        utils.LOGGER.info("Authenticate to accept Xcode license.")

        try:  # ensure xcode license is accepted
            self.shell.execute("sudo xcodebuild -license accept", info=True)
        except utils.shell.ShellError as ex:
            utils.LOGGER.error("Failed to accept Xcode license: %s", ex)
            utils.LOGGER.error(
                "Ensure Xcode is installed using: xcode-select --install"
            )
            raise typer.Abort()
