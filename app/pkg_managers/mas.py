"""MAS package manager module."""

__all__ = ["MAS"]

from app import utils

from .brew import Brew
from .pkg_manager import PackageManager


class MAS(PackageManager):
    """Mac App Store."""

    def is_supported(self) -> bool:
        return utils.MACOS

    def _setup(self) -> None:
        Brew().install("mas")

    def _update(self) -> None:
        self.shell.execute("mas upgrade")
