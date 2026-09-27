"""Gleason work machine manifest."""

from pathlib import Path

from app.env import PLATFORM
from app.models import Machine, Package, Platform
from config import dev, shell, system, terminal

manifest = Machine(
    env={
        "DEV": Path.home() / "Dev",
        "DEV_BIN": Path.home() / "Dev" / "bin",
        "GEMS_DEV": Path.home() / "Dev" / "GEMS",
        "MC_HOSTNAME": "mfareedrmt1",
    },
    modules=(
        [
            system,
            shell,
            dev,
        ]
        if PLATFORM == Platform.WSL
        else [
            system,
            shell,
            terminal,
            dev,
        ]
    ),
    packages=[
        Package(name="vs-professional", winget="microsoft.visualstudio.professional"),
        Package(name="power-toys", winget="microsoft.powertoys"),
        Package(name="sys-internals", winget="microsoft.sysinternals.suite"),
        Package(name="advanced-system-settings", winget="9N8MHTPHNGVV"),
        Package(name="craft-docs", winget="LukiLabs.Craft"),
    ],
)
