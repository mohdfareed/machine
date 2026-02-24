"""Homelab Docker service deployment module.

Deploys Docker Compose services from:
  config/homelab/docker/   — shared services (dockge)
  machines/<id>/docker/    — machine-specific services

Syncs into ~/.homelab/<service>/. Runtime data stays outside the repo.
See config/homelab/README.md for full documentation.
"""

from machine.core import is_macos
from machine.manifest import Module, Package, cask

module = Module(
    packages=[
        # Tailscale — VPN mesh for service networking
        *(
            cask("tailscale")
            if is_macos
            else [
                Package(name="tailscale", script="curl -fsSL https://tailscale.com/install.sh | sh")
            ]
        ),
        # Docker — container runtime for services
        *(
            # NOTE: Docker Desktop cask ("docker") only delivers an Intel binary via
            # Homebrew as of 2026-02. Install Docker Desktop manually on Apple Silicon
            # until the cask ships a universal/ARM build.
            # cask("docker")
            []
            if is_macos
            else [Package(name="docker", script="curl -fsSL https://get.docker.com | sh")]
        ),
    ],
)
