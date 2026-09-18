"""1Password client module."""

from pathlib import Path

from app.env import PLATFORM
from app.models import FileMapping, Module, Package, Platform

match PLATFORM:
    case Platform.WIN:
        _1pass_path = "%LOCALAPPDATA%/1Password/config/ssh"
    case _:  # Unix
        _1pass_path = "~/.config/1Password/ssh"

module = Module(
    files=[
        FileMapping(source="agent.toml", target=Path(_1pass_path) / "agent.toml"),
    ],
    packages=[
        Package(name="1password", cask="1password", winget="AgileBits.1Password"),
        Package(name="1password-cli", cask="1password-cli", winget="AgileBits.1Password.CLI"),
    ],
)
