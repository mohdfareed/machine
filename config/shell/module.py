"""Shell configuration module.

Deploys zsh and PowerShell configs to well-known paths. Installs
shell tools via brew/apt.
"""

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, apt, brew

module = Module(
    files=[
        # zsh
        FileMapping(source=".zshenv", target="~/.zshenv"),
        FileMapping(source=".zshrc", target="~/.zshrc"),
        FileMapping(source=".aliases.sh", target="~/.aliases"),
        # powershell
        FileMapping(source="profile.ps1", target="~/.config/powershell/profile.ps1"),
        FileMapping(source="aliases.ps1", target="~/.config/powershell/aliases.ps1"),
    ],
    packages=[
        *brew("zsh", "fzf", "bat", "eza", "btop", "oh-my-posh"),
        *(apt("unzip") if PLATFORM == Platform.LINUX else []),
    ],
    overrides={
        # zsh
        ".zshrc": "~/.zshrc.local",
        ".zshenv": "~/.zshenv.local",
        # powershell
        "profile.ps1": "~/.config/powershell/profile.local.ps1",
    },
)
