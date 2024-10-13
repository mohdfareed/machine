"""VSCode setup module."""

import shutil

import typer

from app import config, env, utils
from app.pkg_managers import Brew, PackageManager, SnapStore, Winget
from app.utils import LOGGER

plugin_app = typer.Typer(name="ssh", help="Configure SSH keys.")
shell = utils.Shell()

vscode: str
"""The path to the VSCode user settings directory."""


@plugin_app.command()
def setup(
    configuration: config.DefaultConfigArg = config.Default(),
) -> None:
    """Setup VSCode on a new machine."""
    LOGGER.info("Setting up VSCode...")
    PackageManager.from_spec(
        [
            (Brew, lambda: Brew().install("visual-studio-code", cask=True)),
            (Winget, lambda: Winget().install("Microsoft.VisualStudioCode")),
            (SnapStore, lambda: SnapStore().install("code", classic=True)),
        ]
    )

    for file in configuration.vscode.iterdir():
        (env.Default().VSCODE / file.name).unlink(missing_ok=True)
        file.link_to(env.Default().VSCODE / file.name)
    LOGGER.debug("VSCode was setup successfully.")


@plugin_app.command()
def setup_tunnels(name: str) -> None:
    """Setup VSCode SSH tunnels as a service."""
    if not shutil.which("code"):
        LOGGER.error("VSCode is not installed.")
        raise typer.Abort

    LOGGER.info("Setting up VSCode SSH tunnels...")
    cmd = f"code tunnel service install " f"--accept-server-license-terms --name {name}"
    shell.execute(cmd, info=True)
    LOGGER.debug("VSCode SSH tunnels were setup successfully.")
