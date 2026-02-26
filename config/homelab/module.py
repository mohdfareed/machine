"""Homelab Docker service deployment module."""

from machine.core import is_macos
from machine.manifest import Module, Package, cask

module = Module(
    packages=[
        *(
            cask("tailscale")
            if is_macos
            else [
                Package(name="tailscale", script="curl -fsSL https://tailscale.com/install.sh | sh")
            ]
        ),
        *(
            # NOTE: Docker Desktop cask only delivers an Intel binary via Homebrew.
            # Install Docker Desktop manually on Apple Silicon.
            []
            if is_macos
            else [Package(name="docker", script="curl -fsSL https://get.docker.com | sh")]
        ),
    ],
)
