"""Shell configuration module.

Deploys zsh and PowerShell configs to well-known paths. Installs
shell tools via brew/apt.
"""

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package, apt, brew

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
        # powershell (windows and linux)
        FileMapping(source="profile.ps1", target="~/.config/powershell/profile.ps1"),
        FileMapping(source="aliases.ps1", target="~/.config/powershell/aliases.ps1"),
    ],
    packages=[
        *brew("zsh", "fzf", "bat", "eza", "btop"),
        Package(name="oh-my-posh", brew="oh-my-posh", winget="JanDeDobbeleer.OhMyPosh"),
        *(apt("unzip") if PLATFORM == Platform.LINUX else []),
    ],
    overrides=[
        # zsh
        FileMapping(source=".zshrc", target="~/.zshrc.local"),
        FileMapping(source=".zshenv", target="~/.zshenv.local"),
        # powershell
        FileMapping(source="profile.ps1", target="~/.config/powershell/profile.local.ps1"),
    ],
)
