"""Windows PC machine manifest."""

from machine.manifest import MachineManifest, Package

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "ssh-server", "vscode", "vscode-server", "win-term", "core"],
    packages=[
        # Dev tools
        Package(name="tailscale", winget="tailscale.tailscale"),
        Package(name="docker", winget="docker.DockerDesktop"),
        Package(name="power-toys", winget="microsoft.PowerToys"),
        # Utilities
        Package(name="Steam", winget="valve.Steam"),
        Package(name="UniGetUI", winget="martiCliment.UniGetUI"),
        Package(name="iCloud", winget="9PKTQ5699M62"),
        Package(name="Apple Music", winget="9pfhdd62mxs1"),
        Package(name="Xbox Accessories", winget="9nblggh30xj3"),
    ],
)
