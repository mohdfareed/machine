"""Tailscale setup module."""

import os
import shutil
import urllib.request

from typer.main import Typer

from app import utils
from app.models import PluginException
from app.plugins.pkg_managers import Brew
from app.plugins.plugin import Plugin, SetupFunc
from app.utils import LOGGER


class Tailscale(Plugin[None, None]):
    """Configure Tailscale."""

    def __init__(self) -> None:
        super().__init__(None, None)

    @property
    def plugin_setup(self) -> SetupFunc:
        return self._setup

    def app(self) -> Typer:
        plugin_app = super().app()
        plugin_app.command()(self.update)
        return plugin_app

    def _setup(self) -> None:
        LOGGER.info("Setting up tailscale...")
        if Brew().is_supported():
            Brew().install("tailscale", cask=True)

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
