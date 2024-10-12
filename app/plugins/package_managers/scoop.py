"""Scoop package manager module."""

__all__ = ["Scoop"]

from app import utils
from app.utils import LOGGER

from .models import PackageManager


class Scoop(PackageManager):
    """Scoop package manager."""

    @classmethod
    @utils.setup_wrapper
    def setup(cls) -> None:
        Scoop.shell.execute(
            "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
        )
        Scoop.shell.execute('iex "& {$(irm get.scoop.sh)} -RunAsAdmin"')

    @classmethod
    @utils.update_wrapper
    def update(cls) -> None:
        Scoop.shell.execute("scoop update")
        Scoop.shell.execute("scoop update *")

    @classmethod
    @utils.cleanup_wrapper
    def cleanup(cls) -> None:
        Scoop.shell.execute("scoop cleanup *")

    @classmethod
    @utils.is_supported_wrapper
    def is_supported(cls) -> bool:
        return utils.WINDOWS

    @staticmethod
    def add_bucket(bucket: str) -> None:
        """Add a bucket to the scoop package manager."""
        LOGGER.info("Adding bucket %s to scoop...", bucket)
        Scoop.shell.execute(f"scoop bucket add {bucket}", throws=False)
        LOGGER.debug("Bucket %s was added successfully.", bucket)
