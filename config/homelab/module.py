"""Homelab Docker service deployment module."""

from app.models import Module, Package, Platform

module = Module(
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
            winget="Docker.DockerDesktop",
            cmd="curl -fsSL https://get.docker.com | sh",
            platforms=[Platform.LINUX, Platform.MACOS, Platform.WINDOWS],
        ),
    ],
)
