"""Gleason work machine manifest."""

from machine.manifest import MachineManifest, winget

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "vscode", "vscode-tunnel", "terminal", "system"],
    packages=[
        # Dev tools
        *winget("golang.Go"),
        *winget("microsoft.DotNet.SDK"),
        *winget("docker.DockerDesktop"),
        *winget("microsoft.PowerToys"),
        # Admin tools
        *winget("microsoft.sysinternals"),
    ],
    env={},
)
