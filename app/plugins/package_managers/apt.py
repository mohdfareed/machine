"""Apt package manager module."""

__all__ = ["APT"]

import shutil
from typing import Union

from app.utils import LOGGER

from .models import PackageManager


class APT(PackageManager):
    """Advanced Package Tool (APT) package manager."""

    def setup(self) -> None:
        APT.shell.execute("sudo apt update && sudo apt upgrade -y")

    @PackageManager.installer
    def install(self, package: Union[str, list[str]]) -> None:
        APT.shell.execute(f"sudo apt install -y {package}")

    @staticmethod
    def is_supported() -> bool:
        return shutil.which("apt") is not None

    @staticmethod
    def add_keyring(keyring: str, repo: str, name: str) -> None:
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

    def cleanup(self) -> None:
        APT.shell.execute("sudo apt autoremove -y")
