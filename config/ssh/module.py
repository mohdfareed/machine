"""SSH server setup module."""

from app.configuration.models import FileMapping, Module

from config import shell

module = Module(
    depends=[shell],
    files=[FileMapping(source="authorized_keys", target="~/.ssh/authorized_keys", mode=0o600)],
)
