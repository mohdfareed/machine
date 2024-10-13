"""Setup module containing a `setup` function for setting up Tailscale on a new machine."""

__all__ = ["setup"]

import os
import shutil
import urllib.request

import typer

from app import utils
from app.models import PluginException
from app.utils import LOGGER

from .package_managers import Brew

plugin_app = typer.Typer(name="tailscale", help="Configure Tailscale.")
shell = utils.Shell()


@plugin_app.command()
def setup() -> None:
    """Setup tailscale on a new machine."""
    LOGGER.info("Setting up tailscale...")
    if Brew().is_supported():
        Brew().install("tailscale", cask=True)

    elif utils.LINUX:
        if not shutil.which("tailscale"):
            utils.Shell().execute(
                "curl -fsSL https://tailscale.com/install.sh | sh", info=True
            )

    elif utils.WINDOWS:
        installer_url = "https://pkgs.tailscale.com/stable/tailscale-setup.exe"
        installer_path = os.path.join(os.environ["TEMP"], "tailscale-setup.exe")
        urllib.request.urlretrieve(installer_url, installer_path)
        utils.Shell().execute(
            f"Start-Process -FilePath {installer_path} -ArgumentList '/quiet' -Wait",
            throws=False,
        )
        os.remove(installer_path)

    else:
        raise PluginException("Unsupported operating system")
    utils.Shell().execute("sudo tailscale update", info=True)
    LOGGER.debug("Tailscale was setup successfully.")
