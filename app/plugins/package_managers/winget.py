"""WinGet package manager module."""

__all__ = ["WinGet"]

from app import utils

from .models import PackageManager


class WinGet(PackageManager):
    """WinGet package manager."""

    @classmethod
    @utils.update_wrapper
    def update(cls) -> None:
        WinGet.shell.execute("winget upgrade --all --include-unknown")

    @classmethod
    @utils.install_wrapper
    def install(cls, package: str) -> None:
        WinGet.shell.execute(f"winget install -e --id {package}", throws=False)

    @classmethod
    @utils.is_supported_wrapper
    def is_supported(cls) -> bool:
        return cls.is_available()
