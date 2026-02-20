"""Shell configuration module.

Deploys zsh and PowerShell configs to well-known paths. Installs
shell tools via brew/apt.
"""

from machine.manifest import FileMapping, Module, apt, brew

module = Module(
    files=[
        FileMapping(source="zshenv", target="~/.zshenv"),
        FileMapping(source="zshrc", target="~/.zshrc"),
        FileMapping(source="aliases.sh", target="~/.aliases"),
        FileMapping(source="profile.ps1", target="~/.config/powershell/profile.ps1"),
        FileMapping(source="aliases.ps1", target="~/.aliases.ps1"),
    ],
    packages=[
        *brew("zsh", "fzf", "bat", "eza", "btop", "oh-my-posh"),
        *apt("unzip"),  # oh-my-posh dependency
    ],
    overrides={
        ".zshrc.local": "~/.zshrc.local",
        ".zshenv.local": "~/.zshenv.local",
    },
)
