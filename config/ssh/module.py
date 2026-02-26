"""SSH client module."""

from machine.manifest import FileMapping, Module

module = Module(
    files=[
        FileMapping(source="ssh.config", target="~/.ssh/config"),
    ],
)
