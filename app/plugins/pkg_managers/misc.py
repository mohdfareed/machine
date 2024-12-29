"""PIPx package manager module."""

__all__ = ["PIPx"]

from .linux import APT
from .macos import Brew
from .pkg_manager import PkgManager
from .windows import Scoop


class PIPx(PkgManager):
    """PIPx package manager."""

    @classmethod
    def is_supported(cls) -> bool:
        return True

    def setup(self) -> None:
        if APT.is_supported():
            return APT().install("pipx")
        if Brew.is_supported():
            return Brew().install("pipx")
        if Scoop.is_supported():
            return Scoop().install("pipx")
        return None

    def update(self) -> None:
        self.shell.execute("pipx upgrade-all")
