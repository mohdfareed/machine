"""Apt package manager module."""

__all__ = ["APT"]

from app import utils
from app.utils import LOGGER

from .models import PackageManager


class APT(PackageManager):
    """Advanced Package Tool (APT) package manager."""

    @classmethod
    @utils.setup_wrapper
    def setup(cls) -> None:
        pass

    @classmethod
    @utils.update_wrapper
    def update(cls) -> None:
        APT.shell.execute("sudo apt update && sudo apt upgrade -y")

    @classmethod
    @utils.cleanup_wrapper
    def cleanup(cls) -> None:
        APT.shell.execute("sudo apt autoremove -y")

    @classmethod
    @utils.is_supported_wrapper
    def is_supported(cls) -> bool:
        return cls.is_available()

    @classmethod
    def add_keyring(cls, keyring: str, repo: str, name: str) -> None:
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
