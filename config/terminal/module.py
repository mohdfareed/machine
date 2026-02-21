"""Windows Terminal configuration module."""

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

module = Module(
    files=(
        [
            FileMapping(
                source="settings.json",
                target="%LOCALAPPDATA%/Packages"
                "/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json",
            )
        ]
        if PLATFORM == Platform.WINDOWS
        else []
    ),
    packages=[
        Package(name="windows-terminal", winget="microsoft.WindowsTerminal"),
    ],
    overrides=(
        {
            "terminal.settings.json": "%LOCALAPPDATA%"
            "/Microsoft/Windows Terminal/Fragments/settings.local.json"
        }
        if PLATFORM == Platform.WINDOWS
        else {}
    ),
)
