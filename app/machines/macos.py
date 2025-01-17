"""macOS machine."""

__all__ = ["MacOS"]

from pathlib import Path

import typer

from app import config, env, plugins, utils
from app.machine import MachinePlugin
from app.models import PluginProtocol
from app.plugins import pkg_managers
from app.plugins.private_files import PrivateDirArg

PAM_SUDO_PATH = Path("/") / "etc" / "pam.d" / "sudo_local"
PAM_SUDO_CONTENT = """
auth       sufficient     pam_tid.so
""".strip()
VSCODE_TUNNELS_NAME = "macbook"


class MacOS(MachinePlugin[config.MacOS, env.MacOS]):
    """macOS machine configuration."""

    shell = utils.Shell()

    @property
    def _config(self) -> config.MacOS:
        return config.MacOS()

    @property
    def _env(self) -> env.MacOS:
        return env.MacOS(env_file=self._config.zshenv)

    @property
    def plugins(self) -> list[type[PluginProtocol]]:
        return [
            plugins.Fonts,
            plugins.Git,
            plugins.Private,
            plugins.ZSH,
            plugins.SSH,
            plugins.Btop,
            plugins.NeoVim,
            plugins.PowerShell,
            plugins.Tailscale,
            plugins.Docker,
            plugins.Node,
            plugins.Python,
            plugins.VSCode,
        ]

    @classmethod
    def is_supported(cls) -> bool:
        return utils.MACOS

    def setup(self, private_dir: PrivateDirArg = None) -> None:
        super().setup()
        plugins.Private(self.config, self.env).ssh_keys(private_dir)
        plugins.Private(self.config, self.env).env_file(private_dir)
        plugins.VSCode(self.config, self.env).setup_tunnels(VSCODE_TUNNELS_NAME)
        plugins.SSH(self.config, self.env).setup_server()
        self.setup_brew()
        self.system_preferences()
        self.enable_touch_id()

    def setup_brew(self) -> None:
        """Setup Homebrew and install packages."""
        brew = pkg_managers.Brew()
        brew.install_brewfile(self.config.brewfile)
        brew.install("go")
        brew.install_cask("dotnet-sdk godot-mono")

    def system_preferences(self) -> None:
        """Open macOS System Preferences."""
        utils.LOGGER.info("Opening System Preferences...")
        self.shell.execute(
            (
                f"HOSTNAME={self.config.hostname} && "
                f". {self.config.system_preferences}"
            )
        )

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
