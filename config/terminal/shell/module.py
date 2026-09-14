"""Shell configuration module."""

from pathlib import Path

from app.env import PLATFORM
from app.models import FileMapping, Module, Package, Platform

match PLATFORM:
    case Platform.WINDOWS:
        _pwsh_base = Path("~/Documents/PowerShell")
    case _:
        _pwsh_base = Path("~/.config/powershell")


module = Module(
    files=[
        # zsh (unix)
        FileMapping(source=".zshenv", target="~/.zshenv", platforms=[Platform.UNIX]),
        FileMapping(source=".zshrc", target="~/.zshrc", platforms=[Platform.UNIX]),
        FileMapping(source=".zimrc", target="~/.zimrc", platforms=[Platform.UNIX]),
        FileMapping(source=".aliases.sh", target="~/.aliases", platforms=[Platform.UNIX]),
        # powershell (windows and unix)
        FileMapping(source="profile.ps1", target=str(_pwsh_base / "profile.ps1")),
        FileMapping(source="aliases.ps1", target=str(_pwsh_base / "aliases.ps1")),
    ],
    packages=[
        # zsh
        Package(brew="zsh", apt="zsh"),
        Package(brew="fzf", apt="fzf"),
        # powershell
        Package(
            cask="powershell@preview",
            snap="powershell",
            snap_classic=True,
            winget="microsoft.powershell",
        ),
        # utilities
        Package(brew="eza", winget="eza-community.eza"),
        Package(brew="bat", winget="sharkdp.bat"),
        Package(brew="oh-my-posh", winget="JanDeDobbeleer.OhMyPosh"),
        # tools
        Package(apt="unzip"),
        Package(brew="btop", snap="btop", scoop="btop-lhm"),
        Package(brew="fastfetch", winget="fastfetch", apt="fastfetch"),
        # fonts
        Package(
            name="jetbrains-mono",
            cask="font-jetbrains-mono-nerd-font",
            winget="DEVCOM.JetBrainsMonoNerdFont",
        ),
    ],
)
