"""1Password client module."""

from app.env import PLATFORM
from app.models import FileMapping, Module, Package, Platform

match PLATFORM:
    case Platform.MAC:
        _1pass_path = "~/Library/Application Support/1Password/ssh"
    case Platform.WIN:
        _1pass_path = "%LOCALAPPDATA%/1Password/config/ssh"
    case _:  # Linux
        _1pass_path = "~/.config/1password/ssh"

module = Module(
    files=[
        FileMapping(source="agent.toml", target=f"{_1pass_path}/agent.toml"),
    ],
    packages=[
        Package(name="1password", cask="1password", winget="AgileBits.1Password"),
        Package(name="1password-cli", cask="1password-cli", winget="AgileBits.1Password.CLI"),
    ],
)
