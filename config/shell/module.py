"""Shell configuration module."""

from pathlib import Path

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

match PLATFORM:
    case Platform.WINDOWS:
        _pwsh_base = Path("~/Documents/PowerShell")
    case _:
        _pwsh_base = Path("~/.config/powershell")


module = Module(
    files=[
        *(
            []
            if PLATFORM == Platform.WINDOWS
            else [
                FileMapping(source=".zshenv", target="~/.zshenv"),
                FileMapping(source=".zshrc", target="~/.zshrc"),
                FileMapping(source=".aliases.sh", target="~/.aliases"),
            ]
        ),
        # powershell (windows and unix)
        FileMapping(source="profile.ps1", target=str(_pwsh_base / "profile.ps1")),
        FileMapping(source="aliases.ps1", target=str(_pwsh_base / "aliases.ps1")),
    ],
    packages=[
        Package(brew="zsh"),
        Package(brew="fzf"),
        Package(brew="bat"),
        Package(brew="eza"),
        Package(brew="btop"),
        Package(apt="unzip"),
        Package(
            cask="powershell",
            snap="powershell --classic",
            winget="microsoft.powershell",
        ),
        Package(brew="oh-my-posh", winget="JanDeDobbeleer.OhMyPosh"),
    ],
    overrides=[
        # zsh
        FileMapping(source=".zshrc", target="~/.zshrc.local"),
        FileMapping(source=".zshenv", target="~/.zshenv.local"),
        # powershell
        FileMapping(source="profile.ps1", target=str(_pwsh_base / "profile.local.ps1")),
    ],
)
