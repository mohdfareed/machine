"""Scoop package manager module."""

__all__ = ["Scoop"]

import typer

from app import utils
from app.utils import LOGGER

from .package_manager import PackageManager


class Scoop(PackageManager):
    """Scoop package manager."""

    def is_supported(self) -> bool:
        return utils.WINDOWS

    def _setup(self) -> None:
        self.shell.execute(
            "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
        )
        self.shell.execute('iex "& {$(irm get.scoop.sh)} -RunAsAdmin"')

    def _update(self) -> None:
        self.shell.execute("scoop update")
        self.shell.execute("scoop update *")

    def _cleanup(self) -> None:
        self.shell.execute("scoop cleanup *")

    def add_bucket(self, bucket: str) -> None:
        """Add a bucket to the scoop package manager."""
        LOGGER.info("Adding bucket %s to scoop...", bucket)
        self.shell.execute(f"scoop bucket add {bucket}", throws=False)
        LOGGER.debug("Bucket %s was added successfully.", bucket)

    def app(self) -> typer.Typer:
        manager_app = super().app()
        manager_app.command()(self.add_bucket)
        return manager_app
