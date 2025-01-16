"""Btop setup module."""

__all__ = [
    "Fonts",
    "Tailscale",
    "Python",
    "VSCode",
    "NeoVim",
    "Docker",
    "Node",
    "Btop",
    "Zed",
]

import os
import shutil
import urllib.request
from pathlib import Path
from typing import Any, Optional, Protocol

import typer

from app import models, utils
from app.models import PluginException
from app.plugin import Plugin
from app.plugins.pkg_managers import APT, Brew, PIPx, Scoop, SnapStore, Winget
from app.utils import LOGGER

# region: - Configurations and Environments


class PythonEnv(models.EnvironmentProtocol, Protocol):
    """Python environment variables."""

    COMPLETIONS_PATH: Optional[Path]


class VSCodeConfig(models.ConfigProtocol, Protocol):
    """VSCode configuration files."""

    vscode: Path
    """The path to the VSCode user settings directory."""


class VSCodeEnv(models.EnvironmentProtocol, Protocol):
    """VSCode environment variables."""

    VSCODE: Path
    """The path to the VSCode user settings directory."""


class NeoVimConfig(models.ConfigProtocol, Protocol):
    """NeoVim configuration files."""

    vim: Path


class NeoVimEnv(models.EnvironmentProtocol, Protocol):
    """NeoVim environment variables."""

    VIM: Path


class ZedConfig(models.ConfigProtocol, Protocol):
    """Zed configuration files."""

    zed_settings: Path


class ZedEnv(models.EnvironmentProtocol, Protocol):
    """Zed environment variables."""

    ZED_SETTINGS: Path


class GhosttyConfig(models.ConfigProtocol, Protocol):
    """Ghostty configuration files."""

    ghostty: Path


class GhosttyEnv(models.EnvironmentProtocol, Protocol):
    """Ghostty environment variables."""

    GHOSTTY: Path


# endregion


# MARK: - Plugins


class Fonts(Plugin[Any, Any]):
    """Setup fonts on a new machine."""

    def setup(self) -> None:
        LOGGER.info("Setting up fonts...")
        if Brew.is_supported():
            Brew().install("font-computer-modern font-jetbrains-mono-nerd-font")
        elif APT.is_supported():
            APT().install("fonts-jetbrains-mono fonts-lmodern")
        elif Scoop.is_supported():
            Scoop().add_bucket("nerd-fonts").install("nerd-fonts/JetBrains-Mono")
        else:
            utils.LOGGER.error("No supported package manager found.")
            raise typer.Abort

        LOGGER.debug("Fonts were setup successfully.")


class Tailscale(Plugin[None, None]):
    """Configure Tailscale."""

    shell = utils.Shell()

    def setup(self) -> None:
        """Set up tailscale."""
        LOGGER.info("Setting up tailscale...")
        if Brew.is_supported():
            Brew().install_cask("tailscale")

        elif utils.LINUX:
            if not shutil.which("tailscale"):
                self.shell.execute(
                    "curl -fsSL https://tailscale.com/install.sh | sh", info=True
                )

        elif utils.WINDOWS:
            installer_url = "https://pkgs.tailscale.com/stable/tailscale-setup.exe"
            installer_path = Path(os.environ["TEMP"]) / "tailscale-setup.exe"
            urllib.request.urlretrieve(installer_url, installer_path)
            self.shell.execute(
                f"Start-Process -FilePath {installer_path} -ArgumentList '/quiet' -Wait",
                throws=False,
            )
            os.remove(installer_path)

        else:
            raise PluginException("Unsupported operating system")

    def update(self) -> None:
        """Update tailscale."""
        result = self.shell.execute("sudo tailscale update", info=True, throws=False)
        if not result.returncode == 0:
            LOGGER.warning("Failed to update tailscale.")
        LOGGER.debug("Tailscale was setup successfully.")


class Python(Plugin[None, PythonEnv]):
    """Setup Python on a new machine."""

    def setup(self) -> None:
        LOGGER.info("Setting up Python...")

        if Brew.is_supported():
            Brew().install("python pipx pyenv")
        elif APT.is_supported():
            APT().install("python3 python3-pip python3-venv pipx")
            if not shutil.which("pyenv"):
                utils.Shell().execute("curl https://pyenv.run | bash")
        elif Scoop.is_supported():
            Scoop().install("pipx pyenv")

        PIPx().install("poetry")
        if utils.UNIX and shutil.which("poetry"):
            utils.Shell().execute(
                f"poetry completions zsh > {self.env.COMPLETIONS_PATH}/_poetry"
            )
        LOGGER.debug("Python was setup successfully.")


class VSCode(Plugin[VSCodeConfig, VSCodeEnv]):
    """Configure VSCode."""

    shell = utils.Shell()

    def setup(self) -> None:
        """Set up VSCode."""
        LOGGER.info("Setting up VSCode...")
        self.install()
        for file in self.config.vscode.iterdir():
            utils.link(file, self.env.VSCODE / file.name)
        LOGGER.debug("VSCode was setup successfully.")

    def link(self) -> None:
        """Link VSCode configuration files."""
        for file in self.config.vscode.iterdir():
            utils.link(file, self.env.VSCODE / file.name)

    def install(self) -> None:
        """Install VSCode extensions."""
        LOGGER.info("Installing VSCode...")
        if Brew.is_supported():
            Brew().install_cask("visual-studio-code")
        elif Winget.is_supported():
            Winget().install("Microsoft.VisualStudioCode")
        elif SnapStore.is_supported():
            SnapStore().install_classic("code")
        else:
            utils.LOGGER.error("No supported package manager found.")
            raise typer.Abort

    def setup_tunnels(self, name: str) -> None:
        """Setup VSCode SSH tunnels as a service."""
        if not shutil.which("code"):
            LOGGER.error("VSCode is not installed.")
            raise typer.Abort

        LOGGER.info("Setting up VSCode SSH tunnels...")
        cmd = (
            f"code tunnel service install "
            f"--accept-server-license-terms --name {name}"
        )
        self.shell.execute(cmd, info=True)
        LOGGER.debug("VSCode SSH tunnels were setup successfully.")


class NeoVim(Plugin[NeoVimConfig, NeoVimEnv]):
    """Install NeoVim on a machine."""

    def setup(self) -> None:
        """Set up NeoVim."""

        if Brew.is_supported():
            Brew().install("nvim lazygit ripgrep fd")

        elif Winget.is_supported():
            Winget().install(
                "Neovim.Neovim JesseDuffield.lazygit BurntSushi.ripgrep sharkdp.fd"
            )

        elif SnapStore.is_supported():
            SnapStore().install("nvim lazygit-gm ")
            SnapStore().install_classic("ripgrep")
            APT().install("fd-find")

        utils.link(self.config.vim, self.env.VIM)
        LOGGER.debug("NeoVim setup complete.")


class Docker(Plugin[Any, Any]):
    """Setup Docker on a new machine."""

    def setup(self) -> None:
        LOGGER.info("Setting up Docker...")
        if utils.MACOS and utils.ARM:
            LOGGER.warning("Docker is not supported on Apple Silicon.")
            LOGGER.warning("Download manually from: https://www.docker.com")

        elif utils.UNIX:
            utils.Shell().execute("curl -fsSL https://get.docker.com | sh")
        elif utils.WINDOWS:
            Winget().install("Docker.DockerDesktop")

        else:
            raise PluginException("Unsupported operating system")
        LOGGER.debug("Docker was setup successfully.")


class Btop(Plugin[Any, Any]):
    """Install Btop on a machine."""

    def setup(self) -> None:
        if Brew.is_supported():
            Brew().install("btop")
        elif SnapStore.is_supported():
            SnapStore().install("btop")
        elif Scoop.is_supported():
            Scoop().install("btop-lhm")


class Node(Plugin[Any, Any]):
    """Setup Node on a new machine."""

    def setup(self) -> None:
        """Set up Ghostty."""
        self.install()

    def install(self) -> None:
        """Install Node."""
        LOGGER.info("Installing Node...")
        if Brew.is_supported():
            Brew().install("nvm")
        elif Winget.is_supported():
            Winget().install("Schniz.fnm")
        elif utils.LINUX and not shutil.which("nvm"):
            url = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh"
            utils.Shell().execute(f"curl -o- {url} | bash")
        else:
            raise PluginException("Unsupported operating system")
        LOGGER.debug("Node was setup successfully.")


class Zed(Plugin[ZedConfig, ZedEnv]):
    """Setup the Zed text editor on a new machine."""

    def setup(self) -> None:
        LOGGER.info("Setting up Zed...")
        if utils.WINDOWS:
            raise PluginException("Zed is not supported on Windows.")
        if Brew.is_supported():
            Brew().install("zed")
        else:
            utils.Shell().execute("curl -f https://zed.dev/install.sh | sh")

        utils.link(self.config.zed_settings, self.env.ZED_SETTINGS)
        LOGGER.debug("Zed was setup successfully.")


class Ghostty(Plugin[GhosttyConfig, GhosttyEnv]):
    """Install Ghostty on a machine."""

    def setup(self) -> None:
        """Set up Ghostty."""
        LOGGER.info("Setting up Ghostty...")
        self.install()
        self.link()
        LOGGER.debug("Ghostty was setup successfully.")

    def link(self) -> None:
        """Link Ghostty configuration files."""
        utils.link(self.config.ghostty, self.env.GHOSTTY)

    def install(self) -> None:
        """Install Ghostty."""
        LOGGER.info("Setting up Ghostty...")
        if Brew.is_supported():
            Brew().install_cask("ghostty")
        else:
            LOGGER.error("No supported package manager found.")
            raise typer.Abort
        LOGGER.debug("Ghostty was setup successfully.")
