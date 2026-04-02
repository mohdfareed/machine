"""Zed editor configuration module."""

from pathlib import Path

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

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
        FileMapping(source="bookmark_add.py", target=str(_base / "bookmark_add.py")),
    ],
    packages=[
        Package(
            name="zed",
            cask="zed",
            script="curl -f https://zed.dev/install.sh | sh",  # linux only
            winget="ZedIndustries.Zed",
        ),
    ],
)
