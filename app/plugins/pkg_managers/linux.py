"""Apt package manager module."""

__all__ = ["APT", "SnapStore"]

import shutil
from typing import Union

import typer

from app import utils
from app.utils import LOGGER

from .pkg_manager import PkgManager


class APT(PkgManager):
    """Advanced Package Tool (APT) package manager."""

    @classmethod
    def is_supported(cls) -> bool:
        return shutil.which("apt") is not None

    def update(self) -> None:
        self.shell.execute("sudo apt update && sudo apt upgrade -y")

    def cleanup(self) -> None:
        self.shell.execute("sudo apt autoremove -y")

    def add_keyring(self, keyring: str, repo: str, name: str) -> None:
        """Add a keyring to the apt package manager."""
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
        LOGGER.debug("Keyring %s was added successfully.", keyring)

    def from_url(self, url: str) -> None:
        """Install a package from a URL."""
        if not url.split("/")[-1].endswith(".deb"):
            LOGGER.error("URL must point to a .deb file.")
            raise typer.Abort
        temp_file = utils.create_temp_file()

        self.install("wget")
        self.shell.execute(f"wget {url} -O {temp_file}")
        self.shell.execute(f"sudo dpkg -i {temp_file}")
        self.shell.execute("sudo apt install -f")
        temp_file.unlink()

    def app(self) -> typer.Typer:
        machine_app = super().app()
        machine_app.command()(self.add_keyring)
        machine_app.command()(self.from_url)
        return machine_app


class SnapStore(PkgManager):
    """Snap Store package manager."""

    @classmethod
    def is_supported(cls) -> bool:
        return APT.is_supported()

    def setup(self) -> None:
        APT().install("snapd")
        self.install("snapd")

    def update(self) -> None:
        self.shell.execute("snap refresh")

    def install(self, package: Union[list[str], str], classic: bool = False) -> None:
        self.shell.execute(f"snap install {package} {'--classic' if classic else ''}")
