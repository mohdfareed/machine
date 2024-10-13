"""WinGet package manager module."""

__all__ = ["Winget"]

from app import utils

from .pkg_manager import PackageManager


class Winget(PackageManager):
    """WinGet package manager."""

    def is_supported(self) -> bool:
        return utils.WINDOWS

    def _setup(self) -> None:
        return None

    def _update(self) -> None:
        self.shell.execute("winget upgrade --all --include-unknown")

    def _install(self, package: str) -> None:
        self.shell.execute(f"winget install -e --id {package}", throws=False)
