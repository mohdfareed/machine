"""Homelab Docker service deployment module."""

from app.models import Module, Package, Platform

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
