"""SSH client module."""

from app.env import PLATFORM
from app.models import FileMapping, Module, Platform

match PLATFORM:
    case Platform.MAC:
        _config = "config.mac"
    case Platform.WIN | Platform.WSL:
        _config = "config.win"  # WSL uses ssh.exe
    case _:  # Linux
        _config = "config"

module = Module(
    files=[
        FileMapping(source=_config, target="~/.ssh/config", mode=0o600),
    ],
)
