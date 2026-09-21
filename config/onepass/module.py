"""1Password desktop, CLI, SSH agent, and Git signing configuration."""

import platform
from pathlib import Path

from app.env import PLATFORM
from app.models import FileMapping, Module, Package, Platform

match PLATFORM:
    case Platform.MAC:
        _1pass_path = "~/.config/1Password/ssh"
        _git_config = "git/config.mac"
        _ssh_config = "ssh/config.mac"
    case Platform.WIN:
        _1pass_path = "%LOCALAPPDATA%/1Password/config/ssh"
        _git_config = "git/config.win"
        _ssh_config = "ssh/config.win"
    case Platform.WSL:
        _1pass_path = "~/.config/1Password/ssh"
        _git_config = "git/config.wsl"
        _ssh_config = "ssh/config.win"
    case _:  # Linux
        _1pass_path = "~/.config/1Password/ssh"
        _git_config = "git/config.linux"
        _ssh_config = "ssh/config.linux"

module = Module(
    files=[
        FileMapping(
            source="ssh/agent.toml",
            target=Path(_1pass_path) / "agent.toml",
            platforms=[] if PLATFORM == Platform.WSL else None,
        ),
        FileMapping(source=_git_config, target="~/.config/git/config.1pass"),
        FileMapping(
            source=_ssh_config,
            target="~/.ssh/config.d/1password",
            mode=0o600,
            # WSL's Git uses ssh.exe and the Windows user's SSH configuration.
            platforms=[] if PLATFORM == Platform.WSL else None,
        ),
    ],
    packages=[
        Package(
            name="1password",
            cask="1password",
            apt="1password",
            winget="AgileBits.1Password",
            # WSL uses the Windows desktop app; Linux desktop requires x86-64.
            platforms=(
                [Platform.MAC, Platform.WIN]
                if PLATFORM == Platform.WSL
                or (PLATFORM.is_a(Platform.LINUX) and platform.machine() != "x86_64")
                else None
            ),
        ),
        Package(
            name="1password-cli",
            cask="1password-cli",
            apt="1password-cli",
            winget="AgileBits.1Password.CLI",
        ),
    ],
)
