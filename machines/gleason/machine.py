"""Gleason work machine manifest."""

from app.env import PLATFORM
from app.models import FileMapping, Machine, Package, PkgManager, Platform
from config import system
from config.development import agents, python, vscode, zed
from config.terminal import emulators, git, shell
from config.terminal.ssh import client

manifest = Machine(
    pkg_managers=[PkgManager.SNAP] if PLATFORM == Platform.WSL else [PkgManager.SCOOP],
    modules=(
        [
            git,
            shell,
            client,
            python,
        ]
        if PLATFORM == Platform.WSL
        else [
            system,
            git,
            shell,
            client,
            emulators,
            python,
            agents,
            vscode,
            zed,
        ]
    ),
    files=[
        FileMapping(source=".gitconfig.personal", target="~/.config/git/config.personal"),
    ],
    packages=[
        Package(name="raycast", cask="raycast", winget="raycast"),
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
