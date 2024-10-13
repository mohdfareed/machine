"""PIPx package manager module."""

__all__ = ["PIPx"]

from .apt import APT
from .brew import Brew
from .package_manager import PackageManager
from .scoop import Scoop


class PIPx(PackageManager):
    """PIPx package manager."""

    def is_supported(self) -> bool:
        return self.is_available()

    def _setup(self) -> None:
        self.from_spec(
            [
                (APT, lambda: APT().install("pipx")),
                (Brew, lambda: Brew().install("pipx")),
                (Scoop, lambda: Scoop().install("pipx")),
            ]
        )

    def _update(self) -> None:
        self.shell.execute("pipx upgrade-all")
