"""Raspberry Pi machine manifest."""

from machine.manifest import (
    MachineManifest,
    Package,
    snap,
)

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "ssh-server", "vscode", "vscode-tunnel", "core"],
    packages=[
        *snap("go --classic"),
        # Script-installed packages
        Package(
            name="dotnet",
            script="curl -s https://dot.net/v1/dotnet-install.sh | "
            "bash -s -- --channel LTS",
        ),
        Package(
            name="docker",
            script="curl -fsSL https://get.docker.com | sh",
        ),
        Package(
            name="tailscale",
            script="curl -fsSL https://tailscale.com/install.sh | sh",
        ),
    ],
    env={"MC_PRIVATE": "~/.ssh"},
)
