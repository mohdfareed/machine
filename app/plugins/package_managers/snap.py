"""SnapStore package manager module."""

__all__ = ["SnapStore"]

from typing import Union

from .apt import APT
from .models import PackageManager


class SnapStore(PackageManager):
    """Snap Store package manager."""

    def __init__(self, apt: APT) -> None:
        self.apt = apt
        """The Snap Store package manager."""
        super().__init__()

    def setup(self) -> None:
        self.apt.install("snapd")
        self.install("snapd")

    @PackageManager.installer
    def install(self, package: Union[str, list[str]], classic: bool = False) -> None:
        SnapStore.shell.execute(
            f"sudo snap install {package} {'--classic' if classic else ''}"
        )

    def cleanup(self) -> None:
        pass

    @staticmethod
    def is_supported() -> bool:
        return True
