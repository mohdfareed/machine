"""SSH client module."""

from app.models import FileMapping, Module

module = Module(
    overrides=[
        FileMapping(source="ssh.config", target="~/.ssh/config", mode=0o600),
    ],
)
