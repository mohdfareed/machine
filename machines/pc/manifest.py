"""Windows PC machine manifest."""

from machine.manifest import MachineManifest, winget

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "vscode", "vscode-tunnel", "terminal", "system"],
    packages=[
        # Networking
        *winget("tailscale.tailscale"),
        # Dev tools
        *winget("docker.DockerDesktop"),
        *winget("microsoft.PowerToys"),
        # Gaming
        *winget("valve.Steam", "valve.SteamLink"),
        # Utilities
        *winget("martiCliment.UniGetUI"),
        *winget("9PKTQ5699M62"),  # iCloud
        *winget("9pfhdd62mxs1"),  # Apple Music
        *winget("9nblggh30xj3"),  # Xbox Accessories
    ],
    env={"MC_PRIVATE": "%USERPROFILE%\\iCloudDrive\\.machine"},
)
