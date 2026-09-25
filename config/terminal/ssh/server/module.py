"""SSH server setup module."""

from app.env import PLATFORM
from app.models import FileMapping, Module, Package, Platform

from config.terminal import shell
from config.terminal.ssh import client as ssh_client

module = Module(
    depends=[ssh_client, shell] if PLATFORM == Platform.WIN else [ssh_client],
    files=[FileMapping(source="authorized_keys", target="~/.ssh/authorized_keys", mode=0o600)],
    packages=[Package(apt="openssh-server")],
)
