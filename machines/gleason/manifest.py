"""Gleason work machine manifest."""

from machine.manifest import MachineManifest, Package

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "vscode", "win-term", "core"],
    packages=[
        Package(name="go", winget="golang.Go"),
        Package(name="dotnet", winget="microsoft.DotNet.SDK"),
        Package(name="docker", winget="docker.DockerDesktop"),
        Package(name="power-toys", winget="microsoft.PowerToys"),
        Package(name="sys-internals", winget="microsoft.sysinternals"),
        Package(name="UniGetUI", winget="martiCliment.UniGetUI"),
    ],
)
