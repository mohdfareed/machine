"""Raycast launcher configuration module."""

from machine.manifest import FileMapping, Module, Package

module = Module(
    files=[
        FileMapping(source="providers.yaml", target="~/.config/raycast/ai/providers.yaml"),
    ],
    packages=[
        Package(name="uv", brew="uv", winget="astral-sh.uv"),
        Package(name="raycast", cask="raycast", winget="raycast"),
        Package(name="raycast-safari-ext", mas=6738274497),
        Package(name="chatmock", script="uv tool install chatmock"),
    ],
)
