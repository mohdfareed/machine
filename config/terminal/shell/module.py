"""Shell configuration module."""

from pathlib import Path

from app.env import PLATFORM
from app.models import FileMapping, Module, Package, Platform

match PLATFORM:
    case Platform.WIN:
        _pwsh_base = Path("~/Documents/PowerShell")
    case _:
        _pwsh_base = Path("~/.config/powershell")

module = Module(
    files=[
        # zsh
        FileMapping(source="zsh/.zshenv", target="~/.zshenv", platforms=[Platform.UNIX]),
        FileMapping(source="zsh/.zshrc", target="~/.zshrc", platforms=[Platform.UNIX]),
        FileMapping(source="zsh/.zimrc", target="~/.zimrc", platforms=[Platform.UNIX]),
        FileMapping(source="zsh/.aliases", target="~/.aliases", platforms=[Platform.UNIX]),
        # powershell
        FileMapping(source="pwsh/profile.ps1", target=str(_pwsh_base / "profile.ps1")),
        FileMapping(source="pwsh/aliases.ps1", target=str(_pwsh_base / "aliases.ps1")),
        # prompt
        FileMapping(source="starship.toml", target="~/.config/starship.toml"),
    ],
    overrides=[
        # zsh
        FileMapping(source=".zshenv", target="~/.zshenv.mc", platforms=[Platform.UNIX]),
        FileMapping(source=".zshrc", target="~/.zshrc.mc", platforms=[Platform.UNIX]),
        # powershell
        FileMapping(source="pwsh/profile.ps1", target=str(_pwsh_base / "profile.ps1")),
    ],
    packages=[
        # shell
        Package(brew="zsh"),
        Package(brew="zimfw"),
        Package(cask="powershell@preview", winget="microsoft.powershell"),
        Package(brew="starship", winget="Starship.Starship"),  # prompt theme
        # utilities
        Package(brew="eza", winget="eza-community.eza"),  # ls replacement
        Package(brew="bat-extras", winget="sharkdp.bat"),  # cat replacement
        Package(brew="fd", winget="sharkdp.fd"),  # title search
        Package(brew="ripgrep", winget="BurntSushi.ripgrep.MSVC"),  # content search
        Package(brew="fzf", winget="junegunn.fzf"),  # fuzzy finder
        # system
        Package(brew="btop", scoop="btop-lhm"),  # monitoring
        Package(brew="fastfetch", winget="Fastfetch-cli.Fastfetch"),  # information
        # fonts
        Package(
            name="jetbrains-mono",
            cask="font-jetbrains-mono-nerd-font",
            winget="DEVCOM.JetBrainsMonoNerdFont",
        ),
    ],
)
