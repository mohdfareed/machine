"""MAS package manager module."""

__all__ = ["MAS"]


from app import utils

from .brew import Brew
from .models import PackageManager


class MAS(PackageManager):
    """Mac App Store."""

    @classmethod
    @utils.setup_wrapper
    def setup(cls) -> None:
        Brew.install("mas")

    @classmethod
    @utils.update_wrapper
    def update(cls) -> None:
        MAS.shell.execute("mas upgrade")

    @classmethod
    @utils.is_supported_wrapper
    def is_supported(cls) -> bool:
        return utils.MACOS
