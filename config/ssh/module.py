"""SSH client module."""

from app.machine import FileMapping, Module

module = Module(
    overrides=[
        FileMapping(source="ssh.config", target="~/.ssh/config", mode=0o600),
    ],
)
