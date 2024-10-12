"""PIPx package manager module."""

__all__ = ["PIPx"]

from typing import Union

from .apt import APT
from .brew import HomeBrew
from .models import PackageManager
from .scoop import Scoop


class PIPx(PackageManager):
    """PIPx package manager."""

    def __init__(self, pkg_manager: Union[HomeBrew, APT, Scoop]) -> None:
        self.pkg_manager = pkg_manager
        """The OS package manager."""
        super().__init__()

    def setup(self) -> None:
        self.pkg_manager.install("pipx")

    @PackageManager.installer
    def install(self, package: Union[str, list[str]]) -> None:
        PIPx.shell.execute(f"pipx install {package}")

    @staticmethod
    def is_supported() -> bool:
        return True
