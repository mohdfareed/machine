"""Raspberry Pi machine manifest."""

from machine.manifest import (
    MachineManifest,
    Package,
    snap,
)

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "vscode", "vscode-tunnel", "system"],
    packages=[
        *snap("go --classic"),
        # Script-installed packages
        Package(
            name="dotnet",
            script="curl -s https://dot.net/v1/dotnet-install.sh | bash",
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
    env={"MC_PRIVATE": "~/.private"},
)
