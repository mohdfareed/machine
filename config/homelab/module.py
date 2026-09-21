"""Homelab Docker service deployment module."""

from app.models import Module, Package, Platform

from config import onepass

module = Module(
    depends=[onepass],
    packages=[
        Package(
            name="tailscale",
            cask="tailscale",
            winget="Tailscale.Tailscale",
            cmd="curl -fsSL https://tailscale.com/install.sh | sh",
            up_cmd=True,
        ),
        Package(
            name="docker",
            cask="docker-desktop",
            cmd="curl -fsSL https://get.docker.com | sh",
            platforms=[Platform.LINUX, Platform.MAC],
        ),
        # Windows Docker is installed by docker.win.ps1 and upgraded by up_docker.win.ps1.
    ],
)
