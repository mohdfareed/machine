"""SSH client module."""

from app.models import FileMapping, Module

module = Module(
    files=[
        FileMapping(
            source="config",
            target="~/.ssh/config",
            mode=0o600,
        ),
    ],
)
