"""SnapStore package manager module."""

__all__ = ["SnapStore"]

from .apt import APT
from .pkg_manager import PackageManager


class SnapStore(PackageManager):
    """Snap Store package manager."""

    def is_supported(self) -> bool:
        return True

    def _setup(self) -> None:
        APT().install("snapd")
        self.install("snapd")

    def _update(self) -> None:
        self.shell.execute("snap refresh")

    def _install(self, package: str, classic: bool = False) -> None:
        self.shell.execute(f"snap install {package} {'--classic' if classic else ''}")
