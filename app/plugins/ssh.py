"""SSH setup module."""

import shutil
from dataclasses import dataclass
from pathlib import Path

import typer

from app import config, env, utils
from app.pkg_managers import APT
from app.utils import LOGGER

plugin_app = typer.Typer(name="ssh", help="Configure SSH keys.")
shell = utils.Shell()

PUBLIC_EXT: str = ".pub"
"""The extension of the public key filenames."""
PRIVATE_EXT: str = ".key"
"""The extension of the private key filenames."""


@plugin_app.command()
def setup(
    ssh_config: utils.OptionalFileArg = None,
    ssh_keys: utils.ReqDirArg = config.Private().ssh_keys,
) -> None:
    """Setup ssh keys and configuration on a new machine. The ssh keys and
    config file are copied from the specified directory."""

    LOGGER.info("Setting up SSH...")
    if ssh_config:  # symlink ssh config file
        utils.link(ssh_config, env.Default().SSH_DIR / "config")

    # read ssh keys from directory
    for key in _load_keys(ssh_keys):
        _setup_key(key, env.Default())  # setup ssh keys
    LOGGER.info("SSH setup complete")


def _load_keys(keys_dir: Path) -> list["_SSHKeyPair"]:
    """Load ssh keys from the specified directory.

    Returns:
        dict[str, SSHKey]: A dict of key names to key pairs.
    """

    # load private keys
    private_keys = [
        _SSHKeyPair(private=file)
        for file in keys_dir.iterdir()
        if file.suffix == PRIVATE_EXT
    ]

    LOGGER.debug("Loaded %d ssh keys.", len(private_keys))
    return private_keys


def _setup_key(key: "_SSHKeyPair", environment: env.Environment) -> None:
    """Setup an ssh key on a machine."""
    LOGGER.info("Setting up SSH key: %s", key.name)

    # symlink private key and set permissions
    utils.link(key.private, environment.SSH_DIR / key.private.name)
    key.private.chmod(0o600)

    if key.public.exists():  # symlink public key and set permissions
        utils.link(key.public, environment.SSH_DIR / key.public.name)
        key.public.chmod(0o644)

    # get key fingerprint
    fingerprint = shell.execute(f"ssh-keygen -lf {key.private}")[1]
    fingerprint = fingerprint.split(" ")[1]
    LOGGER.debug("Key fingerprint: %s", fingerprint)

    if utils.WINDOWS:  # set up ssh agent on windows
        shell.execute("Get-Service ssh-agent | Set-Service -StartupType Automatic")
        shell.execute("Start-Service ssh-agent")
        cmd = f"ssh-add -l | Select-String -Pattern '{fingerprint}'"
    else:  # command to check if key already exists in ssh agent
        cmd = "ssh-add -l | grep -q " + fingerprint

    # add key to ssh agent if it doesn't exist
    if shell.execute(cmd, throws=False)[0] != 0:
        if utils.MACOS:  # add key to keychain on macOS
            shell.execute(f"ssh-add --apple-use-keychain '{key.private}'")

        else:  # add key to ssh agent on other operating systems
            shell.execute(f"ssh-add '{key.private}'")
        LOGGER.info("Added key to SSH agent")
    else:
        LOGGER.info("Key already exists in SSH agent")


@plugin_app.command()
def setup_server() -> None:
    """setup an ssh server on a new machine."""
    LOGGER.info("Setting up SSH server...")

    if utils.WINDOWS:
        shell.execute("Add-WindowsCapability -Online -Name OpenSSH.Server")
        shell.execute("Get-Service -Name sshd | Set-Service -StartupType Automatic")
        shell.execute("Start-Service sshd")
        LOGGER.debug("SSH server setup complete.")
        return

    if utils.MACOS:
        try:
            shell.execute("sudo systemsetup -setremotelogin on")
        except utils.ShellError as ex:
            LOGGER.error("Failed to enable SSH server: %s", ex)
            return
        LOGGER.debug("SSH server setup complete.")
        return

    if utils.LINUX:
        APT().install("openssh-server")
        shell.execute("sudo systemctl start ssh")
        shell.execute("sudo systemctl enable ssh")
        LOGGER.debug("SSH server setup complete.")
        return


@plugin_app.command()
def generate_key_pair(
    name: str,
    keys_dir: utils.DirArg = config.Private().ssh_keys,
    email: str = "mohdf.fareed@icloud.com",
    passphrase: str = "",
) -> None:
    """Create a new ssh key pair."""
    LOGGER.info("Creating SSH key pair: %s", name)
    keys_dir.mkdir(parents=True, exist_ok=True)

    # define key paths
    private_key = (keys_dir / name).with_suffix(PRIVATE_EXT)
    public_key = (keys_dir / name).with_suffix(PUBLIC_EXT)

    # check if private key already exists
    if private_key.exists():
        LOGGER.warning("Private key already exists: %s", private_key)

        if not public_key.exists():  # regenerate public key
            shell.execute(f"ssh-keygen -y -f {private_key} > {public_key}")
            LOGGER.info("Public key regenerated: %s", public_key)
        return  # don't overwrite existing key pair

    # generate new key pair
    LOGGER.debug("Generating new key pair...")
    key_args = f"-C '{email}' -f {private_key} -N '{passphrase}'"
    shell.execute(f"ssh-keygen -t ed25519 {key_args}")
    public_key.unlink(missing_ok=True)
    shutil.move(private_key.with_suffix(".pub"), public_key)

    LOGGER.info("SSH key pair generated: %s", name)
    LOGGER.debug("Public key: %s", public_key)
    LOGGER.debug("Private key: %s", private_key)


@dataclass
class _SSHKeyPair:
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
