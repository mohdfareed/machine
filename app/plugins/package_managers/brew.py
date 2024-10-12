"""Brew package manager module."""

__all__ = ["Brew"]


from typing import Union

from app import utils
from app.utils import LOGGER

from .models import PackageManager, PackageManagerException


class Brew(PackageManager):
    """Homebrew package manager."""

    @classmethod
    @utils.setup_wrapper
    def setup(cls) -> None:
        try:  # install homebrew otherwise
            Brew.shell.execute('/bin/bash -c "$(curl -fsSL https://git.io/JIY6g)"')
        except utils.ShellError as ex:
            raise PackageManagerException("Failed to install Homebrew.") from ex

    @classmethod
    @utils.update_wrapper
    def update(cls) -> None:
        Brew.shell.execute("brew update && brew upgrade")

    @classmethod
    @utils.install_wrapper
    def install(cls, package: Union[str, list[str]], cask: bool = False) -> None:
        Brew.shell.execute(f"brew install {'--cask' if cask else ''} {package}")

    @classmethod
    @utils.cleanup_wrapper
    def cleanup(cls) -> None:
        Brew.shell.execute("brew cleanup --prune=all", throws=False)

    @classmethod
    @utils.is_supported_wrapper
    def is_supported(cls) -> bool:
        return utils.MACOS or not utils.ARM

    @classmethod
    def install_brewfile(cls, file: str) -> None:
        """Install Homebrew packages from a Brewfile."""

        LOGGER.info("Installing Homebrew packages from Brewfile...")
        Brew.shell.execute(f"brew bundle install --file={file}")
        LOGGER.debug("Homebrew packages were installed successfully.")
