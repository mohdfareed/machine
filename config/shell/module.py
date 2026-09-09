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
        # zsh (unix)
        FileMapping(source=".zshenv", target="~/.zshenv", platforms=[Platform.UNIX]),
        FileMapping(source=".zshrc", target="~/.zshrc", platforms=[Platform.UNIX]),
        FileMapping(source=".aliases.sh", target="~/.aliases", platforms=[Platform.UNIX]),
        # powershell (windows and unix)
        FileMapping(source="profile.ps1", target=str(_pwsh_base / "profile.ps1")),
        FileMapping(source="aliases.ps1", target=str(_pwsh_base / "aliases.ps1")),
    ],
    packages=[
        # shells
        Package(brew="zsh", apt="zsh"),
        Package(brew="oh-my-posh", winget="JanDeDobbeleer.OhMyPosh"),
        Package(
            cask="powershell@preview",
            snap="powershell --classic",
            winget="microsoft.powershell",
        ),
        # python
        Package(name="python", brew="python", apt="python3", winget="Python.Python.3.14"),
        Package(brew="python-freethreading"),
        Package(
            name="uv",
            brew="uv",
            winget="astral-sh.uv",
            platforms=[Platform.MACOS, Platform.WINDOWS],
        ),
        Package(
            name="uv",
            script="curl -LsSf https://astral.sh/uv/install.sh | sh",
            platforms=[Platform.LINUX, Platform.WSL],
        ),
        # utilities
        Package(brew="fzf"),
        Package(brew="bat"),
        Package(brew="eza"),
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
    overrides=[
        # zsh
        FileMapping(source=".zshrc", target="~/.zshrc.local", platforms=[Platform.UNIX]),
        FileMapping(source=".zshenv", target="~/.zshenv.local", platforms=[Platform.UNIX]),
        # powershell
        FileMapping(source="profile.ps1", target=str(_pwsh_base / "profile.local.ps1")),
    ],
)
