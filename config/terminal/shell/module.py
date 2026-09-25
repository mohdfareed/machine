"""Shell configuration module."""

from app.env import PLATFORM
from app.models import FileMapping, Module, Package, Platform
from platformdirs import user_documents_path
from platformdirs.unix import Unix

match PLATFORM:
    case Platform.WIN:
        _pwsh_base = user_documents_path() / "PowerShell"
    case _:
        _pwsh_base = Unix("powershell").user_config_path

module = Module(
    files=[
        # fish
        FileMapping(
            source="fish/config.fish",
            target=Unix("fish").user_config_path / "config.fish",
            platforms=[Platform.UNIX],
        ),
        FileMapping(
            source="fish/aliases.fish",
            target=Unix("fish").user_config_path / "aliases.fish",
            platforms=[Platform.UNIX],
        ),
        FileMapping(
            source="fish/fish_plugins",
            target=Unix("fish").user_config_path / "fish_plugins",
            platforms=[Platform.UNIX],
        ),
        # powershell
        FileMapping(source="pwsh/profile.ps1", target=_pwsh_base / "profile.ps1"),
        FileMapping(source="pwsh/aliases.ps1", target=_pwsh_base / "aliases.ps1"),
        # prompt
        FileMapping(source="starship.toml", target="~/.config/starship.toml"),
    ],
    overrides=[
        # fish
        FileMapping(
            source="config.fish",
            target=Unix("fish").user_config_path / "config.mc.fish",
            platforms=[Platform.UNIX],
        ),
        # powershell
        FileMapping(source="profile.ps1", target=_pwsh_base / "profile.mc.ps1"),
    ],
    packages=[
        # shell
        Package(brew="fish"),
        Package(brew="fisher"),
        Package(cask="powershell@preview", scoop="pwsh"),
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
