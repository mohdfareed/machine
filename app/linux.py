"""Apt package manager module."""

__all__ = ["APT", "SnapStore"]

import shutil

import typer

from app import utils
from app.pkg_manager import PkgManagerPlugin
from app.utils import LOGGER


class APT(PkgManagerPlugin):
    """Advanced Package Tool (APT) package manager."""

    shell = utils.Shell()

    @classmethod
    def is_supported(cls) -> bool:
        return shutil.which("apt") is not None

    def add_keyring(self, keyring: str, repo: str, name: str) -> None:
        """Add a keyring to the apt package manager."""
        self.setup()
        LOGGER.info("Adding keyring %s to apt...", keyring)
        keyring_path = f"/etc/apt/keyrings/{keyring}"

        APT.shell.execute(
            f"""
                (type -p wget >/dev/null || sudo apt-get install wget -y) \
                && sudo mkdir -p -m 755 /etc/apt/keyrings && wget -qO- \
                {keyring} | sudo tee {keyring_path} > /dev/null \
                && sudo chmod go+r {keyring_path} \
                && echo "deb [arch=$(dpkg --print-architecture) \
                signed-by={keyring_path}] {repo}" | \
                sudo tee /etc/apt/sources.list.d/{name}.list > /dev/null \
                && sudo apt update
            """
        )
        APT.shell.execute("sudo apt update")
        LOGGER.debug("Keyring %s was added successfully.", keyring)

    def from_url(self, url: str) -> None:
        """Install a package from a URL."""
        self.setup()

        if not url.split("/")[-1].endswith(".deb"):
            LOGGER.error("URL must point to a .deb file.")
            raise typer.Abort
        temp_file = utils.create_temp_file()

        self._install("wget")
        self.shell.execute(f"wget {url} -O {temp_file}")
        self.shell.execute(f"sudo dpkg -i {temp_file}")
        self.shell.execute("sudo apt install -f")
        temp_file.unlink()

    def _update(self) -> None:
        self.shell.execute("sudo apt update && sudo apt full-upgrade -y")

    def _cleanup(self) -> None:
        self.shell.execute("sudo apt autoremove -y")

    def _install(self, package: str) -> None:
        self.shell.execute(f"sudo apt install {package} -y")

    def _setup(self) -> None: ...


class SnapStore(PkgManagerPlugin):
    """Snap Store package manager."""

    shell = utils.Shell()

    @classmethod
    def is_supported(cls) -> bool:
        return APT.is_supported()

    @utils.pkg_installer
    def install_classic(self, package: str) -> None:
        """Install a classic snap package."""
        self.setup()
        self._install_pkg(package, classic=True)

    def _setup(self) -> None:
        APT().install("snapd")
        self._install("snapd")

    def _update(self) -> None:
        self.shell.execute("snap refresh")

    def _install(self, package: str) -> None:
        self._install_pkg(package, classic=False)

    def _cleanup(self) -> None: ...

    def _install_pkg(self, package: str, classic: bool) -> None:
        self.shell.execute(
            f"snap install {package} {'--classic' if classic else ''}"
        )
