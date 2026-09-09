"""Homelab Docker service deployment module."""

from app.core import Platform
from app.machine import Module, Package

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
            platforms=[Platform.LINUX],
        ),
        Package(
            name="docker",
            cask="docker-desktop",
            platforms=[Platform.MACOS],
        ),
    ],
)
