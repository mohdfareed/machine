"""Brew package manager module."""

__all__ = ["Brew", "MAS"]

from pathlib import Path

from typing_extensions import override

from app import models, pkg_manager, utils

brew: Path = Path("/home/linuxbrew/.linuxbrew/bin/brew")
if utils.Platform.MACOS and utils.Platform.ARM:
    brew = Path("/opt/homebrew/bin/brew")
elif utils.Platform.MACOS:
    brew = Path("/usr/local/bin/brew")


class Brew(pkg_manager.PkgManagerPlugin):
    """Homebrew package manager."""

    shell = utils.Shell()

    @classmethod
    def is_supported(cls) -> bool:
        return bool(utils.Platform.MACOS) or not bool(utils.Platform.ARM)

    @utils.loading_indicator("Installing packages")
    def install_brewfile(self, filepath: Path) -> None:
        """Install Homebrew packages from a Brewfile."""
        self.setup()
        utils.LOGGER.info("Installing Homebrew packages from: %s", filepath)
        self.shell.execute(f"{brew} bundle install --file={filepath}")
        utils.LOGGER.debug("Homebrew packages were installed successfully.")

    @utils.pkg_installer
    def install_cask(self, package: str) -> None:
        """Install a cask package."""
        self.setup()
        self._install_pkg(package, cask=True)

    @override
    @classmethod
    def is_installed(cls) -> bool:
        return brew.exists()

    def _setup(self) -> None:
        try:  # Install Homebrew
            self.shell.execute(
                '/bin/bash -c "$(curl -fsSL https://git.io/JIY6g)"'
            )
        except utils.ShellError as ex:
            raise models.AppError("Failed to install Homebrew.") from ex

    def _update(self) -> None:
        self.shell.execute(f"{brew} update && {brew} upgrade")

    def _cleanup(self) -> None:
        self.shell.execute("{brew} cleanup --prune=all", throws=False)

    def _install(self, package: str) -> None:
        self._install_pkg(package, cask=False)

    def _install_pkg(self, package: str, cask: bool) -> None:
        self.shell.execute(
            f"{brew} install {'--cask' if cask else ''} {package}"
        )


class MAS(pkg_manager.PkgManagerPlugin):
    """Mac App Store."""

    shell = utils.Shell()

    @classmethod
    def is_supported(cls) -> bool:
        return bool(utils.Platform.MACOS) and Brew.is_supported()

    def _setup(self) -> None:
        Brew().install("mas")

    def _update(self) -> None:
        self.shell.execute("mas upgrade")

    def _install(self, package: str) -> None:
        self.shell.execute(f"mas install {package}")

    def _cleanup(self) -> None: ...
