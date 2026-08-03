"""Windows Terminal configuration module."""

from pathlib import Path

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

CONFIG_DIR = Path(r"%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState")

module = Module(
    files=(
        [FileMapping(source="settings.json", target=str(CONFIG_DIR / "settings.json"))]
        if PLATFORM == Platform.WINDOWS
        else []
    ),
    packages=[
        Package(name="windows-terminal", winget="microsoft.WindowsTerminal"),
    ],
)
