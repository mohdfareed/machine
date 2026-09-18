"""SSH server setup module."""

from app.models import Module, Package

from config.terminal.ssh import client

module = Module(depends=[client], packages=[Package(apt="openssh-server")])
