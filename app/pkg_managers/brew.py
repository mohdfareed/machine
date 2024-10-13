"""Brew package manager module."""

__all__ = ["Brew"]

import typer

from app import utils
from app.models import PackageManagerException
from app.utils import LOGGER

from .pkg_manager import PackageManager, T


class Brew(PackageManager):
    """Homebrew package manager."""

    def is_supported(self) -> bool:
        return utils.MACOS or not utils.ARM

    def _setup(self) -> None:
        try:
            # Install Homebrew
            self.shell.execute('/bin/bash -c "$(curl -fsSL https://git.io/JIY6g)"')
        except utils.ShellError as ex:
            raise PackageManagerException("Failed to install Homebrew.") from ex

    def _update(self) -> None:
        self.shell.execute("brew update && brew upgrade")

    def _cleanup(self) -> None:
        self.shell.execute("brew cleanup --prune=all", throws=False)

    def _install(self, package: str, cask: bool = False) -> None:
        self.shell.execute(f"brew install {'--cask' if cask else ''} {package}")

    def _uninstall(self, package: str) -> None:
        self.shell.execute(f"brew uninstall {package}")

    def install_brewfile(self: T, filepath: str) -> T:
        """Install Homebrew packages from a Brewfile."""
        LOGGER.info("Installing Homebrew packages from Brewfile...")
        self.shell.execute(f"brew bundle install --file={filepath}")
        LOGGER.debug("Homebrew packages were installed successfully.")
        return self

    def app(self) -> typer.Typer:
        machine_app = super().app()
        machine_app.command()(self.install_brewfile)
        return machine_app
