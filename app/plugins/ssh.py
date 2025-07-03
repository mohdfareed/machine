"""SSH setup module."""

__all__ = ["SSH"]

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app import models, utils
from app.plugin import Plugin
from app.utils import LOGGER

from .pkg_managers import APT

PUBLIC_EXT: str = ".pub"
"""The extension of the public key filenames."""
PRIVATE_EXT: str = ""
"""The extension of the private key filenames."""


class SSHConfig(models.ConfigProtocol, Protocol):
    """SSH configuration files."""

    ssh_keys: Path
    ssh_config: Path


class SSHEnv(models.EnvProtocol, Protocol):
    """SSH environment variables."""

    SSH_DIR: Path


class SSH(Plugin[SSHConfig, SSHEnv]):
    """Configure SSH keys."""

    shell = utils.Shell()

    def _setup(self) -> None:
        if self.config.ssh_config:  # symlink ssh config file
            utils.link(self.config.ssh_config, self.env.SSH_DIR / "config")

        # read ssh keys from directory
        for key in self.load_keys(self.config.ssh_keys):
            # symlink private key and set permissions
            utils.link(key.private, self.env.SSH_DIR / key.private.name)
            key.private.chmod(0o600)

            if key.public.exists():  # symlink public key and set permissions
                utils.link(key.public, self.env.SSH_DIR / key.public.name)
                key.public.chmod(0o644)
            self.load_key(key, self.shell)

    def setup_server(self) -> None:
        """Setup an SSH server on a new machine."""
        LOGGER.info("Setting up SSH server...")

        if utils.Platform.WINDOWS:
            self.shell.execute(
                "Add-WindowsCapability -Online -Name OpenSSH.Server"
            )
            self.shell.execute(
                "Get-Service -Name sshd | Set-Service -StartupType Automatic"
            )
            self.shell.execute("Start-Service sshd")
            LOGGER.debug("SSH server setup complete.")
            return

        if utils.Platform.MACOS:
            try:
                self.shell.execute("sudo systemsetup -setremotelogin on")
            except utils.ShellError as ex:
                LOGGER.error("Failed to enable SSH server: %s", ex)
                return
            LOGGER.debug("SSH server setup complete.")
            return

        if utils.Platform.LINUX:
            APT().install("openssh-server")
            self.shell.execute("sudo systemctl start ssh")
            self.shell.execute("sudo systemctl enable ssh")
            LOGGER.debug("SSH server setup complete.")
            return

    def generate_key_pair(
        self,
        name: str,
        email: str = "mohdf.fareed@icloud.com",
        passphrase: str = "",
    ) -> None:
        """Create a new ssh key pair."""
        LOGGER.info("Creating SSH key pair: %s", name)
        self.env.SSH_DIR.mkdir(parents=True, exist_ok=True)

        # define key paths
        private_key = (self.env.SSH_DIR / name).with_suffix(PRIVATE_EXT)
        public_key = (self.env.SSH_DIR / name).with_suffix(PUBLIC_EXT)

        # check if private key already exists
        if private_key.exists():
            LOGGER.warning("Private key already exists: %s", private_key)

            if not public_key.exists():  # regenerate public key
                self.shell.execute(
                    f"ssh-keygen -y -f {private_key} > {public_key}"
                )
                LOGGER.info("Public key regenerated: %s", public_key)
            return  # don't overwrite existing key pair

        # generate new key pair
        LOGGER.debug("Generating new key pair...")
        key_args = f"-C '{email}' -f {private_key} -N '{passphrase}'"
        self.shell.execute(f"ssh-keygen -t ed25519 {key_args}")
        public_key.unlink(missing_ok=True)
        shutil.move(private_key.with_suffix(".pub"), public_key)

        LOGGER.info("SSH key pair generated: %s", name)
        LOGGER.debug("Public key: %s", public_key)
        LOGGER.debug("Private key: %s", private_key)

    def setup_key(self, name: str) -> None:
        """Setup an ssh key on a machine."""
        LOGGER.info("Setting up SSH key: %s", name)
        key = SSHKeyPair(private=self.env.SSH_DIR / name)
        self.load_key(key, self.shell)

    @staticmethod
    def load_key(key: "SSHKeyPair", shell: utils.Shell) -> None:
        """Setup an ssh key on a machine."""
        LOGGER.info("Loading SSH key: %s", key.name)

        # get key fingerprint
        fingerprint = shell.execute(f"ssh-keygen -lf {key.private}")[1]
        fingerprint = fingerprint.split(" ")[1]
        LOGGER.debug("Key fingerprint: %s", fingerprint)

        if utils.Platform.WINDOWS:  # set up ssh agent on windows
            shell.execute(
                "Get-Service ssh-agent | Set-Service -StartupType Automatic"
            )
            shell.execute("Start-Service ssh-agent")
            cmd = f"ssh-add -l | Select-String -Pattern '{fingerprint}'"
        else:  # command to check if key already exists in ssh agent
            cmd = "ssh-add -l | grep -q " + fingerprint

        # add key to ssh agent if it doesn't exist
        if shell.execute(cmd, throws=False)[0] != 0:
            if utils.Platform.MACOS:  # add key to keychain on macOS
                shell.execute(f"ssh-add --apple-use-keychain '{key.private}'")

            else:  # add key to ssh agent on other operating systems
                shell.execute(f"ssh-add '{key.private}'")
            LOGGER.info("Added key to SSH agent")
        else:
            LOGGER.info("Key already exists in SSH agent")

    @staticmethod
    def load_keys(keys_dir: Path) -> list["SSHKeyPair"]:
        """Load ssh keys from the specified directory.

        Returns:
            dict[str, SSHKey]: A dict of key names to key pairs.
        """

        # load private keys
        private_keys = [
            SSHKeyPair(private=file)
            for file in keys_dir.iterdir()
            if file.suffix == PRIVATE_EXT
        ]

        LOGGER.info("Loaded %d ssh keys.", len(private_keys))
        return private_keys


@dataclass
class SSHKeyPair:
    """An SSH key pair of a private and optional public keys."""

    private: Path
    """The path to the private key file."""

    @property
    def public(self) -> Path:
        """The path to the public key file."""
        return (self.private.parent / self.name).with_suffix(PUBLIC_EXT)

    @property
    def name(self) -> str:
        """The name of the key pair based on the private key filename."""
        return self.private.name.removesuffix(PRIVATE_EXT)
