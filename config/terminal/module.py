"""Terminal apps configuration module."""

import os
from pathlib import Path

from app.config.models import FileMapping, Module, Package, Platform
from app.runtime.env import PLATFORM

_local_app_data = Path("~") / "AppData" / "Local"
if PLATFORM == Platform.WIN:
    _local_app_data = Path(os.environ["LOCALAPPDATA"])

module = Module(
    files=[
        # Ghostty configuration file mapping.
        FileMapping(
            source="config.ghostty",
            target="~/.config/ghostty/config.ghostty",
            platforms=[Platform.MAC],
        ),
        # Windows Terminal configuration file mapping.
        FileMapping(
            source="win-term.json",
            target=_local_app_data
            / "Packages"
            / "Microsoft.WindowsTerminal_8wekyb3d8bbwe"
            / "LocalState"
            / "settings.json",
            platforms=[Platform.WIN],
        ),
    ],
    packages=[
        Package(name="ghostty", cask="ghostty"),
        Package(name="windows-terminal", winget="microsoft.WindowsTerminal"),
        Package(
            name="jetbrains-mono",
            cask="font-jetbrains-mono-nerd-font",
            winget="DEVCOM.JetBrainsMonoNerdFont",
        ),
    ],
)
