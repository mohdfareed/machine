"""Zed editor configuration module."""

from pathlib import Path

from app.env import PLATFORM
from app.models import FileMapping, Module, Package, Platform

match PLATFORM:
    case Platform.WINDOWS:
        _base = Path(r"%APPDATA%") / "Zed"
    case _:  # macos/linux
        _base = Path("~/.config/zed")


module = Module(
    files=[
        FileMapping(source="keymap.json", target=str(_base / "keymap.json")),
        FileMapping(source="settings.json", target=str(_base / "settings.json")),
        FileMapping(source="snippets.json", target=str(_base / "snippets" / "snippets.json")),
        FileMapping(source="tasks.json", target=str(_base / "tasks.json")),
    ],
    packages=[
        Package(
            cask="zed",
            winget="ZedIndustries.Zed",
            platforms=[Platform.MACOS, Platform.WINDOWS],
        ),
        Package(
            name="zed",
            cmd="curl -f https://zed.dev/install.sh | sh",
            up_cmd=True,
            platforms=[Platform.LINUX],
        ),
        Package(
            brew="shellcheck",
            apt="shellcheck",
            winget="koalaman.shellcheck",
        ),
    ],
)
