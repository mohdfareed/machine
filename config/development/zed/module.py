"""Zed editor configuration module."""

from pathlib import Path

from app.env import PLATFORM
from app.models import FileMapping, Module, Package, Platform

match PLATFORM:
    case Platform.WIN:
        _base = Path(r"%APPDATA%") / "Zed"
    case _:  # macos/linux
        _base = Path("~/.config/zed")


module = Module(
    files=[
        FileMapping(source="keymap.json", target=_base / "keymap.json"),
        FileMapping(source="settings.json", target=_base / "settings.json"),
        FileMapping(source="snippets.json", target=_base / "snippets" / "snippets.json"),
        FileMapping(source="tasks.json", target=_base / "tasks.json"),
    ],
    packages=[
        Package(
            cask="zed",
            winget="ZedIndustries.Zed",
            platforms=[Platform.MAC, Platform.WIN],
        ),
        Package(
            name="zed",
            cmd="curl -f https://zed.dev/install.sh | sh",
            up_cmd=True,
            platforms=[Platform.LINUX],
        ),
        # Extension dependencies.
        Package(
            brew="shellcheck",
            apt="shellcheck",
            winget="koalaman.shellcheck",
        ),
    ],
)
