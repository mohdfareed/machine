"""Zed editor configuration module (macOS/Linux only)."""

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

match PLATFORM:
    case Platform.MACOS:
        _base = "~/.config/zed"
    case Platform.WINDOWS:
        _base = "%APPDATA%/Zed"
    case _:
        _base = "~/.config/zed"

module = Module(
    files=([FileMapping(source="settings.json", target=f"{_base}/settings.json")]),
    packages=[
        Package(
            name="zed",
            brew="zed --cask",
            script="curl -f https://zed.dev/install.sh | sh",
            winget="ZedIndustries.Zed",
        ),
    ],
)
