"""Windows package managers."""

__all__ = ["Winget", "Scoop"]


import typer

from app import utils
from app.utils import LOGGER

from .pkg_manager import PkgManager


class Winget(PkgManager):
    """WinGet package manager."""

    @classmethod
    def is_supported(cls) -> bool:
        return utils.WINDOWS

    def setup(self) -> None:
        return None

    def update(self) -> None:
        self.shell.execute("winget upgrade --all --include-unknown")

    def install(self, package: str) -> None:
        self.shell.execute(f"winget install -e --id {package}", throws=False)


class Scoop(PkgManager):
    """Scoop package manager."""

    @classmethod
    def is_supported(cls) -> bool:
        return Winget.is_supported()

    def setup(self) -> None:
        self.shell.execute(
            "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
        )
        self.shell.execute('iex "& {$(irm get.scoop.sh)} -RunAsAdmin"')

    def update(self) -> None:
        self.shell.execute("scoop update")
        self.shell.execute("scoop update *")

    def cleanup(self) -> None:
        self.shell.execute("scoop cleanup *")

    def add_bucket(self, bucket: str) -> "Scoop":
        """Add a bucket to the scoop package manager."""
        LOGGER.info("Adding bucket %s to scoop...", bucket)
        self.shell.execute(f"scoop bucket add {bucket}", throws=False)
        LOGGER.debug("Bucket %s was added successfully.", bucket)
        return self

    def app(self) -> typer.Typer:
        manager_app = super().app()
        manager_app.command()(self.add_bucket)
        return manager_app
