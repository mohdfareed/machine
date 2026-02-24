"""Raspberry Pi machine manifest."""

from machine.manifest import (
    MachineManifest,
    Package,
    snap,
)

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "ssh-server", "vscode", "vsc-tunnel", "homelab", "core"],
    files=[],
    packages=[
        *snap("go --classic"),
        # Script-installed packages
        Package(
            name="dotnet",
            script="curl -s https://dot.net/v1/dotnet-install.sh | bash -s -- --channel LTS",
        ),
    ],
)
