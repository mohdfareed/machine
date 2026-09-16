"""SSH server setup module."""

from app.models import Module, Package

module = Module(depends=["terminal.ssh.client"], packages=[Package(apt="openssh-server")])
