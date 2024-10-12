"""PIPx package manager module."""

__all__ = ["PIPx"]

from app import utils

from .apt import APT
from .brew import Brew
from .models import PackageManager, PackageManagerException
from .scoop import Scoop


class PIPx(PackageManager):
    """PIPx package manager."""

    @classmethod
    @utils.setup_wrapper
    def setup(cls) -> None:
        for store in cls.available(Brew, APT, Scoop):
            store.install("pipx")
            break
        raise PackageManagerException("No package manager found.")
