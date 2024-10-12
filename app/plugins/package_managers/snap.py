"""SnapStore package manager module."""

__all__ = ["SnapStore"]

from typing import Union

from app import utils

from .apt import APT
from .models import PackageManager


class SnapStore(PackageManager):
    """Snap Store package manager."""

    @classmethod
    def command(cls) -> str:
        """The package manager's shell command."""
        return "snap"

    @classmethod
    @utils.setup_wrapper
    def setup(cls) -> None:
        APT.install("snapd")
        cls.install("snapd")

    @classmethod
    @utils.install_wrapper
    def install(cls, package: Union[str, list[str]], classic: bool = False) -> None:
        SnapStore.shell.execute(
            f"snap install {package} {'--classic' if classic else ''}"
        )

    @classmethod
    @utils.is_supported_wrapper
    def is_supported(cls) -> bool:
        return True
