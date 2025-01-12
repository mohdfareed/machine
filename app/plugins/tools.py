"""Btop setup module."""

import shutil

from app import utils
from app.models import PluginException
from app.plugins.pkg_managers import (
    APT,
    Brew,
    Scoop,
    SnapStore,
    Winget,
    install_from_specs,
)
from app.plugins.plugin import Plugin
from app.utils import LOGGER


class Fonts(Plugin[None, None]):
    """Setup fonts on a new machine."""

    def __init__(self) -> None:
        super().__init__(None, None)

    def setup(self) -> None:
        LOGGER.info("Setting up fonts...")
        install_from_specs(
            [
                (
                    Brew,
                    lambda: Brew().install(
                        "font-computer-modern font-jetbrains-mono-nerd-font"
                    ),
                ),
                (APT, lambda: APT().install("fonts-jetbrains-mono fonts-lmodern")),
                (
                    Scoop,
                    lambda: Scoop()
                    .add_bucket("nerd-fonts")
                    .install("nerd-fonts/JetBrains-Mono"),
                ),
            ]
        )
        LOGGER.debug("Fonts were setup successfully.")


class Docker(Plugin[None, None]):
    """Setup Docker on a new machine."""

    def __init__(self) -> None:
        super().__init__(None, None)

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


class Btop(Plugin[None, None]):
    """Install Btop on a machine."""

    def __init__(self) -> None:
        super().__init__(None, None)

    def setup(self) -> None:
        if Brew.is_supported():
            Brew().install("btop")
        elif SnapStore.is_supported():
            SnapStore().install("btop")
        elif Scoop.is_supported():
            Scoop().install("btop-lhm")


class Node(Plugin[None, None]):
    """Setup Node on a new machine."""

    def __init__(self) -> None:
        super().__init__(None, None)

    def setup(self) -> None:
        LOGGER.info("Setting up Node...")

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
