"""Apt package manager module."""

__all__ = ["APT"]

import typer

from app import utils
from app.models import PackageManagerException
from app.utils import LOGGER

from .package_manager import PackageManager, T


class APT(PackageManager):
    """Advanced Package Tool (APT) package manager."""

    def is_supported(self) -> bool:
        return self.is_available()

    def _setup(self) -> None:
        pass

    def _update(self) -> None:
        self.shell.execute("sudo apt update && sudo apt upgrade -y")

    def _cleanup(self) -> None:
        self.shell.execute("sudo apt autoremove -y")

    def add_keyring(self: T, keyring: str, repo: str, name: str) -> T:
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
        return self

    def from_url(self: T, url: str) -> T:
        """Install a package from a URL."""
        if not url.split("/")[-1].endswith(".deb"):
            raise PackageManagerException("URL must point to a .deb file")
        temp_file = utils.create_temp_file()

        self.install("wget")
        self.shell.execute(f"wget {url} -O {temp_file}")
        self.shell.execute(f"sudo dpkg -i {temp_file}")
        self.shell.execute("sudo apt install -f")
        temp_file.unlink()
        return self

    def app(self) -> typer.Typer:
        machine_app = super().app()
        machine_app.command()(self.add_keyring)
        return machine_app
