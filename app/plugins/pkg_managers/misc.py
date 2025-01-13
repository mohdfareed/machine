"""PIPx package manager module."""

__all__ = ["PIPx"]

from app.pkg_manager import PkgManagerPlugin

from .linux import APT
from .macos import Brew
from .windows import Scoop


class PIPx(PkgManagerPlugin):
    """PIPx package manager."""

    @classmethod
    def is_supported(cls) -> bool:
        return True

    def _setup(self) -> None:
        if APT.is_supported():
            return APT().install("pipx")
        if Brew.is_supported():
            return Brew().install("pipx")
        if Scoop.is_supported():
            return Scoop().install("pipx")
        return None

    def _update(self) -> None:
        self.shell.execute("pipx upgrade-all")

    def _install(self, package: str) -> None:
        self.shell.execute(f"pipx install {package}")

    def _cleanup(self) -> None: ...
