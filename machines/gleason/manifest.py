"""Gleason work machine manifest."""

from machine.manifest import MachineManifest, winget

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "vscode", "win-term", "core"],
    packages=[
        # Dev tools
        *winget("golang.Go"),
        *winget("microsoft.DotNet.SDK"),
        *winget("docker.DockerDesktop"),
        # Utilities
        *winget("microsoft.PowerToys"),
        *winget("microsoft.sysinternals"),
        *winget("martiCliment.UniGetUI"),
    ],
    env={"MC_PRIVATE": "%USERPROFILE%\\.ssh"},
)
