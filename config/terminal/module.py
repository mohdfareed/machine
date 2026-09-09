"""Terminal apps configuration module."""

from pathlib import Path

from app.core import Platform
from app.machine import FileMapping, Module, Package

WIN_TERM_CONFIG = Path(
    r"%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState"
)

module = Module(
    files=[
        FileMapping(
            source="config",
            target="~/.config/ghostty/config",
            platforms=[Platform.MACOS, Platform.LINUX],
        ),
        FileMapping(
            source="settings.json",
            target=str(WIN_TERM_CONFIG / "settings.json"),
            platforms=[Platform.WINDOWS],
        ),
    ],
    packages=[
        Package(name="ghostty", cask="ghostty", snap="ghostty --classic"),
        Package(name="windows-terminal", winget="microsoft.WindowsTerminal"),
    ],
)
