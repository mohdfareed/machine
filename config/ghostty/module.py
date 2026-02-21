"""Ghostty terminal configuration module (macOS/Linux only)."""

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

module = Module(
    files=(
        []
        if PLATFORM == Platform.WINDOWS
        else [FileMapping(source="config", target="~/.config/ghostty/config")]
    ),
    packages=[
        Package(name="ghostty", brew="ghostty --cask", snap="ghostty --classic"),
    ],
)
