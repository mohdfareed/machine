"""Raspberry Pi machine manifest."""

from machine.manifest import MachineManifest, Package

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "ssh-server", "vscode", "vsc-server", "homelab", "core"],
    files=[],
    packages=[
        Package(name="go", snap="go --classic"),
        # Script-installed packages
        Package(
            name="dotnet",
            script="curl -s https://dot.net/v1/dotnet-install.sh | bash -s -- --channel LTS",
        ),
    ],
)
