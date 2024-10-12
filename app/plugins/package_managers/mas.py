"""MAS package manager module."""

__all__ = ["MAS"]

from typing import Union

from app import utils
from app.utils import LOGGER

from .brew import HomeBrew
from .models import PackageManager


class MAS(PackageManager):
    """Mac App Store."""

    def __init__(self, homebrew: HomeBrew) -> None:
        self.homebrew = homebrew
        """The Homebrew package manager."""
        super().__init__()

    def setup(self) -> None:
        self.homebrew.install("mas")
        LOGGER.info("Updating Mac App Store applications...")
        MAS.shell.execute("mas upgrade")

    @PackageManager.installer
    def install(self, package: Union[str, list[str]]) -> None:
        MAS.shell.execute(f"mas install {package}")

    def cleanup(self) -> None:
        pass

    @staticmethod
    def is_supported() -> bool:
        return utils.MACOS
