"""Brew package manager module."""

__all__ = ["Brew", "MAS"]

from pathlib import Path

import typer

from app import utils
from app.models import PackageManagerException
from app.utils import LOGGER

from .pkg_manager import PkgManager


class Brew(PkgManager):
    """Homebrew package manager."""

    @classmethod
    def is_supported(cls) -> bool:
        return utils.MACOS or not utils.ARM

    def setup(self) -> None:
        try:
            # Install Homebrew
            self.shell.execute('/bin/bash -c "$(curl -fsSL https://git.io/JIY6g)"')
        except utils.ShellError as ex:
            raise PackageManagerException("Failed to install Homebrew.") from ex

    def update(self) -> None:
        self.shell.execute("brew update && brew upgrade")

    def cleanup(self) -> None:
        self.shell.execute("brew cleanup --prune=all", throws=False)

    def install(self, package: str, cask: bool = False) -> None:
        self.shell.execute(f"brew install {'--cask' if cask else ''} {package}")

    def install_brewfile(self, filepath: Path) -> None:
        """Install Homebrew packages from a Brewfile."""
        LOGGER.info("Installing Homebrew packages from: %s", filepath)
        self.shell.execute(f"brew bundle install --file={filepath}")
        LOGGER.debug("Homebrew packages were installed successfully.")

    def app(self) -> typer.Typer:
        machine_app = super().app()
        machine_app.command()(self.install_brewfile)
        return machine_app


class MAS(PkgManager):
    """Mac App Store."""

    @classmethod
    def is_supported(cls) -> bool:
        return utils.MACOS

    def setup(self) -> None:
        Brew().install("mas")

    def update(self) -> None:
        self.shell.execute("mas upgrade")
