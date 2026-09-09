"""Raycast launcher configuration module."""

from app.models import FileMapping, Module, Package

module = Module(
    packages=[
        Package(name="raycast", cask="raycast", winget="raycast"),
        Package(name="raycast-safari-ext", mas=6738274497),
    ],
)
