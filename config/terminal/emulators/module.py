"""Terminal apps configuration module."""

from pathlib import Path

from app.models import FileMapping, Module, Package, Platform

WIN_TERM_CONFIG = Path(
    r"%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState"
)

module = Module(
    files=[
        # Ghostty configuration file mapping.
        FileMapping(
            source="config.ghostty",
            target="~/.config/ghostty/config.ghostty",
            platforms=[Platform.MACOS, Platform.LINUX],
        ),
        # Windows Terminal configuration file mapping.
        FileMapping(
            source="win-term.json",
            target=str(WIN_TERM_CONFIG / "settings.json"),
            platforms=[Platform.WINDOWS],
        ),
    ],
    packages=[
        Package(name="ghostty", cask="ghostty", snap="ghostty", snap_classic=True),
        Package(name="windows-terminal", winget="microsoft.WindowsTerminal"),
    ],
)
