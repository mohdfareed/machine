"""Homelab Docker service deployment module."""

from app.models import Module, Package, Platform

from config import onepass, system
from config.terminal import git, shell, ssh

module = Module(
    depends=[
        system,
        onepass,
        git,
        shell,
        ssh,
    ],
    packages=[
        # Networking
        Package(
            name="tailscale",
            cask="tailscale",
            winget="Tailscale.Tailscale",
            cmd="curl -fsSL https://tailscale.com/install.sh | sh",
            up_cmd=True,
        ),
        # Services
        Package(
            name="docker",
            cask="docker-desktop",
            cmd="curl -fsSL https://get.docker.com | sh",
            up_cmd=True,
            platforms=[Platform.LINUX, Platform.MAC],
        ),  # Windows Docker is handled by scripts.
        Package(brew="rsync"),  # file sync
    ],
)
