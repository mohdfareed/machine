"""Raspberry Pi machine manifest."""

from machine.manifest import (
    MachineManifest,
    Package,
    snap,
)

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "ssh-server", "vscode", "vsc-server", "homelab", "core"],
    files=[],
    packages=[
        *snap("go --classic"),
        # Script-installed packages
        Package(
            name="dotnet",
            script="curl -s https://dot.net/v1/dotnet-install.sh | bash -s -- --channel LTS",
        ),
    ],
    env={
        "MC_ENV_FILES": "tailscale",
        "HOMEPAGE_TITLE": "Raspberry Pi",
        "HOMEPAGE_FAVICON": "mdi-raspberry-pi",
    },
)
