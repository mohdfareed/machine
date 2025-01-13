"""Windows package managers."""

__all__ = ["Winget", "Scoop"]


from app import utils
from app.pkg_manager import PkgManagerPlugin
from app.utils import LOGGER


class Winget(PkgManagerPlugin):
    """WinGet package manager."""

    @classmethod
    def is_supported(cls) -> bool:
        return utils.WINDOWS

    def _setup(self) -> None:
        return None

    def _update(self) -> None:
        self.shell.execute("winget upgrade --all --include-unknown")

    def _install(self, package: str) -> None:
        self.shell.execute(f"winget install -e --id {package}", throws=False)

    def _cleanup(self) -> None: ...


class Scoop(PkgManagerPlugin):
    """Scoop package manager."""

    @classmethod
    def is_supported(cls) -> bool:
        return Winget.is_supported()

    def add_bucket(self, bucket: str) -> "Scoop":
        """Add a bucket to the scoop package manager."""
        self.setup()
        LOGGER.info("Adding bucket %s to scoop...", bucket)

        self.shell.execute(f"scoop bucket add {bucket}", throws=False)

        LOGGER.debug("Bucket %s was added successfully.", bucket)
        return self

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

    def _install(self, package: str) -> None:
        self.shell.execute(f"scoop install {package}")
