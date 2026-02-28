"""OpenClaw AI assistant module."""

from machine.manifest import Module, cask

module = Module(
    packages=[
        *cask("openclaw"),
    ],
)
