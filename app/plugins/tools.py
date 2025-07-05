"""Tools setup module."""

__all__ = [
    "Fonts",
    "Tailscale",
    "Python",
    "VSCode",
    "Docker",
    "Node",
    "Zed",
]

import os
import shutil
import urllib.request
from pathlib import Path
from typing import Any, Optional, Protocol

from app import models, utils
from app.plugin import Plugin
from app.plugins.pkg_managers import APT, Brew, PIPx, Scoop, SnapStore, Winget
from app.utils import LOGGER

# region: - Configurations and Environments


class PythonEnv(models.EnvProtocol, Protocol):
    """Python environment variables."""

    COMPLETIONS_PATH: Optional[Path]


class VSCodeConfig(models.ConfigProtocol, Protocol):
    """VSCode configuration files."""

    vscode: Path
    """The path to the VSCode user settings directory."""


class VSCodeEnv(models.EnvProtocol, Protocol):
    """VSCode environment variables."""

    VSCODE: Path
    """The path to the VSCode user settings directory."""


class ZedConfig(models.ConfigProtocol, Protocol):
    """Zed configuration files."""

    zed_settings: Path


class ZedEnv(models.EnvProtocol, Protocol):
    """Zed environment variables."""

    ZED_SETTINGS: Path


class GhosttyConfig(models.ConfigProtocol, Protocol):
    """Ghostty configuration files."""

    ghostty: Path


class GhosttyEnv(models.EnvProtocol, Protocol):
    """Ghostty environment variables."""

    GHOSTTY: Path


# endregion


# MARK: - Plugins


class Fonts(Plugin[Any, Any]):
    """Setup fonts on a new machine."""

    def _setup(self) -> None:
        if Brew.is_supported():
            Brew().install(
                "font-computer-modern font-jetbrains-mono-nerd-font"
            )
        elif APT.is_supported():
            APT().install("fonts-jetbrains-mono fonts-lmodern")
        elif Scoop.is_supported():
            Scoop().add_bucket("nerd-fonts")
            Scoop().install("nerd-fonts/JetBrains-Mono")
        else:
            utils.LOGGER.error("No supported package manager found.")


class Tailscale(Plugin[Any, Any]):
    """Configure Tailscale."""

    shell = utils.Shell()

    def _setup(self) -> None:
        if Brew.is_supported():
            Brew().install_cask("tailscale")

        elif utils.Platform.LINUX:
            if not shutil.which("tailscale"):
                self.shell.execute(
                    "curl -fsSL https://tailscale.com/install.sh | sh",
                    info=True,
                )

        elif utils.Platform.WINDOWS:
            installer_url = (
                "https://pkgs.tailscale.com/stable/tailscale-setup.exe"
            )
            installer_path = Path(os.environ["TEMP"]) / "tailscale-setup.exe"
            urllib.request.urlretrieve(installer_url, installer_path)
            self.shell.execute(
                f"Start-Process -FilePath {installer_path} -ArgumentList '/quiet' -Wait",
                throws=False,
            )
            os.remove(installer_path)

        else:
            utils.LOGGER.error("Unsupported operating system.")

    @utils.loading_indicator("Updating Tailscale")
    def update(self) -> None:
        """Update tailscale."""
        result = self.shell.execute(
            "sudo tailscale update", info=True, throws=False
        )
        if not result.returncode == 0:
            LOGGER.warning("Failed to update tailscale.")
        LOGGER.debug("Tailscale was setup successfully.")

    def status(self) -> None:
        """Check the status of Tailscale."""
        self.shell.execute("tailscale status", info=True)

    def start(self) -> None:
        """Start the Tailscale service."""
        self.shell.execute("sudo tailscale up", info=True)


class Python(Plugin[Any, PythonEnv]):
    """Setup Python on a new machine."""

    def _setup(self) -> None:
        if Brew.is_supported():
            Brew().install("python uv")
        elif APT.is_supported():
            APT().install("python3 uv")
        elif Scoop.is_supported():
            Scoop().install("pipx uv")
        else:
            utils.LOGGER.error("No supported package manager found.")


class VSCode(Plugin[VSCodeConfig, VSCodeEnv]):
    """Configure VSCode."""

    shell = utils.Shell()

    def _setup(self) -> None:
        self.install()
        for file in self.config.vscode.iterdir():
            utils.link(file, self.env.VSCODE / file.name)

    def link(self) -> None:
        """Link VSCode configuration files."""
        for file in self.config.vscode.iterdir():
            utils.link(file, self.env.VSCODE / file.name)

    def install(self) -> None:
        """Install VSCode extensions."""
        if Brew.is_supported():
            Brew().install_cask("visual-studio-code")
        elif Winget.is_supported():
            Winget().install("Microsoft.VisualStudioCode")
        elif SnapStore.is_supported():
            SnapStore().install_classic("code")
        else:
            utils.LOGGER.error("No supported package manager found.")

    def setup_tunnels(self, name: str) -> None:
        """Setup VSCode SSH tunnels as a service."""
        if not shutil.which("code"):
            utils.LOGGER.error("VSCode is not installed.")

        LOGGER.info("Setting up VSCode SSH tunnels...")
        cmd = (
            f"code tunnel service install "
            f"--accept-server-license-terms --name {name}"
        )
        self.shell.execute(cmd, info=True)
        LOGGER.debug("VSCode SSH tunnels were setup successfully.")


class Docker(Plugin[Any, Any]):
    """Setup Docker on a new machine."""

    def _setup(self) -> None:
        if utils.Platform.MACOS and utils.Platform.ARM:
            LOGGER.warning("Docker is not supported on Apple Silicon.")
            LOGGER.warning("Download manually from: https://www.docker.com")

        elif utils.Platform.UNIX:
            utils.Shell().execute("curl -fsSL https://get.docker.com | sh")
        elif utils.Platform.WINDOWS:
            Winget().install("Docker.DockerDesktop")

        else:
            utils.LOGGER.error("Unsupported operating system.")


class Node(Plugin[Any, Any]):
    """Setup Node on a new machine."""

    def _setup(self) -> None:
        self.install()

    def install(self) -> None:
        """Install Node."""
        if Brew.is_supported():
            Brew().install("nvm")
        elif Winget.is_supported():
            Winget().install("Schniz.fnm")
        elif utils.Platform.LINUX and not shutil.which("nvm"):
            url = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh"
            utils.Shell().execute(f"curl -o- {url} | bash")
        else:
            utils.LOGGER.error("Unsupported operating system.")


class Zed(Plugin[ZedConfig, ZedEnv]):
    """Setup the Zed text editor on a new machine."""

    def _setup(self) -> None:
        if utils.Platform.WINDOWS:
            utils.LOGGER.error("Zed is not supported on Windows.")
            return

        if Brew.is_supported():
            Brew().install("zed")
        else:
            utils.Shell().execute("curl -f https://zed.dev/install.sh | sh")
        utils.link(self.config.zed_settings, self.env.ZED_SETTINGS)


class Ghostty(Plugin[GhosttyConfig, GhosttyEnv]):
    """Install Ghostty on a machine."""

    def _setup(self) -> None:
        self.install()
        self.link()

    def link(self) -> None:
        """Link Ghostty configuration files."""
        utils.link(self.config.ghostty, self.env.GHOSTTY)

    def install(self) -> None:
        """Install Ghostty."""
        if Brew.is_supported():
            Brew().install_cask("ghostty")
        else:
            LOGGER.error("No supported package manager found.")
