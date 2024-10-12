"""Brew package manager module."""

__all__ = ["HomeBrew"]


import shutil
from typing import Optional, Union

from app import utils
from app.utils import LOGGER

from .models import PackageManager, PackageManagerException


class HomeBrew(PackageManager):
    """Homebrew package manager."""

    def setup(self) -> None:
        if not shutil.which("brew"):
            LOGGER.info("Installing Homebrew...")
            try:  # install homebrew otherwise
                HomeBrew.shell.execute(
                    '/bin/bash -c "$(curl -fsSL https://git.io/JIY6g)"'
                )
            except utils.ShellError as ex:
                raise PackageManagerException("Failed to install Homebrew.") from ex
        HomeBrew.shell.execute("brew update && brew upgrade")

    @PackageManager.installer
    def install(self, package: Union[str, list[str]], cask: bool = False) -> None:
        HomeBrew.shell.execute(f"brew install {'--cask' if cask else ''} {package}")

    def cleanup(self) -> None:
        HomeBrew.shell.execute("brew cleanup --prune=all", throws=False)

    @staticmethod
    def is_supported() -> bool:
        return utils.MACOS or not utils.ARM

    def install_brewfile(self, file: str) -> None:
        """Install Homebrew packages from a Brewfile."""

        LOGGER.info("Installing Homebrew packages from Brewfile...")
        HomeBrew.shell.execute(f"brew bundle install --file={file}")
        LOGGER.debug("Homebrew packages were installed successfully.")

    @classmethod
    def safe_setup(cls) -> "Optional[HomeBrew]":
        """Safely setup Homebrew without throwing exceptions."""

        try:
            return HomeBrew()
        except PackageManagerException as ex:
            LOGGER.error("Homebrew is not supported: %s", ex)
            return None
