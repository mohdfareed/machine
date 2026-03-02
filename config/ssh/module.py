"""SSH client module."""

from machine.manifest import FileMapping, Module

module = Module(
    overrides=[
        FileMapping(source="ssh.config", target="~/.ssh/config"),
    ],
)
