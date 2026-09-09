"""Windows Terminal configuration module."""

from pathlib import Path

from app.core import Platform
from app.machine import FileMapping, Module, Package

CONFIG_DIR = Path(r"%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState")

module = Module(
    files=[
        FileMapping(
            source="settings.json",
            target=str(CONFIG_DIR / "settings.json"),
            platforms=[Platform.WINDOWS],
        )
    ],
    packages=[
        Package(name="windows-terminal", winget="microsoft.WindowsTerminal"),
    ],
)
