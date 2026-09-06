"""Homelab Docker service deployment module."""

from machine.core import Platform
from machine.manifest import Module, Package

module = Module(
    packages=[
        Package(
            name="tailscale",
            cask="tailscale",
            script="curl -fsSL https://tailscale.com/install.sh | sh",
        ),
        Package(
            name="docker",
            script="curl -fsSL https://get.docker.com | sh",
            platforms=[Platform.LINUX, Platform.WSL],
        ),
        Package(
            name="docker",
            cask="docker-desktop",
            platforms=[Platform.MACOS],
        ),
    ],
)
