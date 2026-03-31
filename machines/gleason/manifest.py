"""Gleason work machine manifest."""

from machine.manifest import MachineManifest, Package

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "vscode", "win-term", "core", "zed", "raycast"],
    packages=[
        Package(name="dotnet", winget="microsoft.DotNet.SDK.10"),
        Package(name="power-toys", winget="microsoft.PowerToys"),
        Package(name="sys-internals", winget="microsoft.sysinternals.suite"),
        Package(name="go", winget="golang.Go"),
        Package(name="docker", winget="docker.DockerDesktop"),
        Package(name="jetbrains-mono", winget="DEVCOM.JetBrainsMonoNerdFont"),
        Package(name="craft-docs", winget="LukiLabs.Craft"),
    ],
)
