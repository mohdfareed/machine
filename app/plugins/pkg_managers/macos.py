"""Brew package manager module."""

__all__ = ["Brew", "MAS"]

from pathlib import Path

from app import utils
from app.models import PackageManagerException
from app.pkg_manager import PkgManagerPlugin
from app.utils import LOGGER


class Brew(PkgManagerPlugin):
    """Homebrew package manager."""

    @classmethod
    def is_supported(cls) -> bool:
        return utils.MACOS or not utils.ARM

    def install_brewfile(self, filepath: Path) -> None:
        """Install Homebrew packages from a Brewfile."""
        self.setup()
        LOGGER.info("Installing Homebrew packages from: %s", filepath)
        self.shell.execute(f"brew bundle install --file={filepath}")
        LOGGER.debug("Homebrew packages were installed successfully.")

    def install_cask(self, package: str) -> None:
        """Install a cask package."""
        self.setup()

        def wrapper(packages: list[str]) -> None:
            LOGGER.info("Installing cask package %s...", packages)
            self._install_pkg(" ".join(packages), cask=True)
            LOGGER.debug("Cask package %s was installed successfully.", packages)

        utils.with_progress("Installing...")(wrapper)(package.split())

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

    def _install(self, package: str) -> None:
        self._install_pkg(package, cask=False)

    def _install_pkg(self, package: str, cask: bool) -> None:
        self.shell.execute(f"brew install {'--cask' if cask else ''} {package}")


class MAS(PkgManagerPlugin):
    """Mac App Store."""

    @classmethod
    def is_supported(cls) -> bool:
        return utils.MACOS

    def _setup(self) -> None:
        Brew().install("mas")

    def _update(self) -> None:
        self.shell.execute("mas upgrade")

    def _install(self, package: str) -> None:
        self.shell.execute(f"mas install {package}")

    def _cleanup(self) -> None: ...
