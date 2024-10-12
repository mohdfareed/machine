"""WinGet package manager module."""

__all__ = ["WinGet"]

import shutil
from typing import Union

from .models import PackageManager


class WinGet(PackageManager):
    """WinGet package manager."""

    def setup(self) -> None:
        WinGet.shell.execute("winget upgrade --all --include-unknown")

    @PackageManager.installer
    def install(self, package: Union[str, list[str]]) -> None:
        WinGet.shell.execute(f"winget install -e --id {package}", throws=False)

    @staticmethod
    def is_supported() -> bool:
        return shutil.which("winget") is not None
