"""Gleason work machine manifest."""

from app.core import PLATFORM, Platform
from app.machine import Machine, Package, PkgManager

manifest = Machine(
    pkg_managers=(
        [PkgManager.APT, PkgManager.SNAP]
        if PLATFORM == Platform.WSL
        else [PkgManager.WINGET, PkgManager.SCOOP]
    ),
    modules=(
        ["git", "shell", "ssh", "codex"]
        if PLATFORM == Platform.WSL
        else ["git", "shell", "ssh", "vscode", "terminal", "system", "zed", "raycast", "codex"]
    ),
    packages=[
        Package(name="vs-professional", winget="microsoft.visualstudio.professional"),
        Package(name="dotnet", winget="microsoft.dotnet.sdk.10"),
        Package(name="power-toys", winget="microsoft.powertoys"),
        Package(name="sys-internals", winget="microsoft.sysinternals.suite"),
        Package(name="advanced-system-settings", winget="9N8MHTPHNGVV"),
        Package(name="docker", winget="docker.DockerDesktop"),
        Package(name="craft-docs", winget="LukiLabs.Craft"),
        Package(name="go", winget="golang.Go", apt="golang-go"),
    ],
)
