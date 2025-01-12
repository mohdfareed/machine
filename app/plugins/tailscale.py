"""Tailscale setup module."""

__all__ = ["Tailscale"]

import os
import shutil
import urllib.request

from app import utils
from app.models import PluginException
from app.plugins.pkg_managers import Brew
from app.plugins.plugin import Plugin
from app.utils import LOGGER, shell


class Tailscale(Plugin[None, None]):
    """Configure Tailscale."""

    shell = shell.Shell()

    def __init__(self) -> None:
        super().__init__(None, None)

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
            installer_path = os.path.join(os.environ["TEMP"], "tailscale-setup.exe")
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
