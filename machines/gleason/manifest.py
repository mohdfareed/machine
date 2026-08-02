"""Gleason work machine manifest."""

from machine.manifest import MachineManifest, Package

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "vscode", "win-term", "core", "zed", "raycast"],
    packages=[
        Package(name="vs-professional", winget="microsoft.visualstudio.professional"),
        Package(name="dotnet", winget="microsoft.dotnet.sdk.10"),
        Package(name="power-toys", winget="microsoft.powertoys"),
        Package(name="sys-internals", winget="microsoft.sysinternals.suite"),
        Package(name="advanced-system-settings", winget="9N8MHTPHNGVV"),
        Package(name="docker", winget="docker.DockerDesktop"),
        Package(name="jetbrains-mono", winget="DEVCOM.JetBrainsMonoNerdFont"),
        Package(name="chatgpt", winget="9NT1R1C2HH7J"),
        Package(name="codex", winget="openai.codex"),
        Package(name="craft-docs", winget="LukiLabs.Craft"),
        Package(name="go", winget="golang.Go"),
    ],
)
