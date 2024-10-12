"""Scoop package manager module."""

__all__ = ["Scoop"]

import shutil
from typing import Union

from app import utils
from app.utils import LOGGER

from .models import PackageManager


class Scoop(PackageManager):
    """Scoop package manager."""

    def setup(self) -> None:
        if not shutil.which("scoop"):  # install
            Scoop.shell.execute(
                "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
            )
            Scoop.shell.execute('iex "& {$(irm get.scoop.sh)} -RunAsAdmin"')

        else:  # update
            Scoop.shell.execute("scoop update")
            Scoop.shell.execute("scoop update *")

    @PackageManager.installer
    def install(self, package: Union[str, list[str]]) -> None:
        Scoop.shell.execute(f"scoop install {package}")

    def cleanup(self) -> None:
        Scoop.shell.execute("scoop cleanup *")

    @staticmethod
    def is_supported() -> bool:
        return utils.WINDOWS

    @staticmethod
    def add_bucket(bucket: str) -> None:
        """Add a bucket to the scoop package manager."""
        LOGGER.info("Adding bucket %s to scoop...", bucket)
        Scoop.shell.execute(f"scoop bucket add {bucket}", throws=False)
        LOGGER.debug("Bucket %s was added successfully.", bucket)
