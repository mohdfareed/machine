"""Ghostty terminal configuration module (Unix only)."""

from app.core import Platform
from app.machine import FileMapping, Module, Package

module = Module(
    files=[
        FileMapping(
            source="config",
            target="~/.config/ghostty/config",
            platforms=[Platform.MACOS, Platform.LINUX],
        )
    ],
    packages=[
        Package(name="ghostty", cask="ghostty", snap="ghostty --classic"),
    ],
)
