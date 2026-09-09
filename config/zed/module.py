"""Zed editor configuration module."""

from pathlib import Path

from app.core import PLATFORM, Platform
from app.machine import FileMapping, Module, Package

match PLATFORM:
    case Platform.WINDOWS:
        _base = Path(r"%APPDATA%") / "Zed"
    case _:  # macos/linux
        _base = Path("~/.config/zed")


module = Module(
    files=[
        FileMapping(source="keymap.json", target=str(_base / "keymap.json")),
        FileMapping(source="profiles.json", target=str(_base / "profiles.json")),
        FileMapping(source="settings.json", target=str(_base / "settings.json")),
        FileMapping(source="snippets.json", target=str(_base / "snippets.json")),
        FileMapping(source="tasks.json", target=str(_base / "tasks.json")),
    ],
    packages=[
        Package(
            name="zed",
            cask="zed",
            winget="ZedIndustries.Zed",
            platforms=[Platform.MACOS, Platform.WINDOWS],
        ),
        Package(
            name="zed",
            script="curl -f https://zed.dev/install.sh | sh",
            platforms=[Platform.LINUX],
        ),
    ],
)
