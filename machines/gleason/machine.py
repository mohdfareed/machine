"""Gleason work machine manifest."""

from pathlib import Path

from app.env import PLATFORM
from app.models import Machine, Package, PkgManager, Platform
from config import system
from config.development import agents, python, vscode, zed
from config.terminal import emulators, git, shell
from config.terminal.ssh import client as ssh_client

_dev = Path.home() / "Dev"

manifest = Machine(
    env={
        "DEV": _dev,
        "DEV_BIN": _dev / "bin",
        "GEMS_DEV": _dev / "GEMS",
        "MC_HOSTNAME": "MFAREEDRMT1",
    },
    pkg_managers=[PkgManager.SNAP] if PLATFORM == Platform.WSL else [PkgManager.SCOOP],
    modules=(
        [git, shell, ssh_client, python, agents]
        if PLATFORM == Platform.WSL
        else [
            system,
            git,
            shell,
            ssh_client,
            emulators,
            python,
            agents,
            vscode,
            zed,
        ]
    ),
    packages=[
        Package(name="vs-professional", winget="microsoft.visualstudio.professional"),
        Package(name="dotnet", winget="microsoft.dotnet.sdk.10"),
        Package(name="power-toys", winget="microsoft.powertoys"),
        Package(name="sys-internals", winget="microsoft.sysinternals.suite"),
        Package(name="advanced-system-settings", winget="9N8MHTPHNGVV"),
        Package(name="craft-docs", winget="LukiLabs.Craft"),
        Package(name="go", winget="golang.Go", brew=" go"),
    ],
)
