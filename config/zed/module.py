"""Zed editor configuration module (macOS/Linux only)."""

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

match PLATFORM:
    case Platform.WINDOWS:
        _base = "%APPDATA%/Zed"
    case _:  # macos/linux
        _base = "~/.config/zed"

module = Module(
    files=[
        FileMapping(source="keymap.json", target=f"{_base}/keymap.json"),
        FileMapping(source="profiles.json", target=f"{_base}/profiles.json"),
        FileMapping(source="settings.json", target=f"{_base}/settings.json"),
        FileMapping(source="snippets.json", target=f"{_base}/snippets.json"),
        FileMapping(source="tasks.json", target=f"{_base}/tasks.json"),
    ],
    packages=[
        Package(
            name="zed",
            brew="zed --cask",
            script="curl -f https://zed.dev/install.sh | sh",  # linux only
            winget="ZedIndustries.Zed",
        ),
    ],
)
