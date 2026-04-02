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
        # NOTE: Docker Desktop cask only delivers an Intel binary via Homebrew.
        #   Install Docker Desktop manually on Apple Silicon.
        Package(
            name="docker",
            script="curl -fsSL https://get.docker.com | sh",
            platforms=[Platform.LINUX, Platform.WSL],
        ),
    ],
)
