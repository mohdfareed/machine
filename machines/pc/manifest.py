"""Windows PC machine manifest."""

from machine.manifest import MachineManifest, winget

manifest = MachineManifest(
    modules=[
        "git",
        "shell",
        "ssh",
        "ssh-server",
        "vscode",
        "win-term",
        "core",
    ],
    packages=[
        # Dev tools
        *winget("tailscale.tailscale"),
        *winget("docker.DockerDesktop"),
        *winget("microsoft.PowerToys"),
        # Utilities
        *winget("valve.Steam"),
        *winget("martiCliment.UniGetUI"),
        *winget("9PKTQ5699M62"),  # iCloud
        *winget("9pfhdd62mxs1"),  # Apple Music
        *winget("9nblggh30xj3"),  # Xbox Accessories
    ],
)
