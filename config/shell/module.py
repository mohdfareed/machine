"""PowerShell, Git, and SSH client configuration."""

from app.config.models import FileMapping, Module, Package, Platform
from app.runtime.env import powershell_config_dir

_pwsh_base = powershell_config_dir()

module = Module(
    files=[
        # powershell
        FileMapping(source="pwsh/profile.ps1", target=_pwsh_base / "profile.ps1"),
        FileMapping(source="pwsh/aliases.ps1", target=_pwsh_base / "aliases.ps1"),
        FileMapping(source="pwsh/completions.ps1", target=_pwsh_base / "completions.ps1"),
        # prompt
        FileMapping(source="starship.toml", target="~/.config/starship.toml"),
        # ssh client
        FileMapping(source="ssh/config", target="~/.ssh/config", mode=0o600),
        # git
        FileMapping(source="git/.gitconfig", target="~/.gitconfig"),
        FileMapping(source="git/.gitignore", target="~/.gitignore"),
        FileMapping(
            source="git/.gitconfig.win",
            target="~/.config/git/config.win",
            platforms=[Platform.WIN],
        ),
    ],
    overrides=[
        # git
        FileMapping(source=".gitconfig", target="~/.config/git/config.mc"),
        # powershell
        FileMapping(source="profile.ps1", target=_pwsh_base / "profile.mc.ps1"),
    ],
    packages=[
        # git
        Package(name="git", brew="git", winget="Git.Git"),
        Package(name="git-lfs", brew="git-lfs", winget="GitHub.GitLFS"),
        # shell
        Package(brew="powershell", cask="powershell@preview", scoop="pwsh"),
        Package(brew="carapace", winget="rsteube.Carapace"),  # command completions
        Package(brew="starship", winget="Starship.Starship"),  # prompt theme
        # files
        Package(brew="micro", winget="zyedidia.micro"),  # text editor
        Package(brew="eza", winget="eza-community.eza"),  # ls replacement
        Package(brew="bat-extras", winget="sharkdp.bat"),  # cat replacement
        # search
        Package(brew="fd", winget="sharkdp.fd"),  # title search
        Package(brew="ripgrep", winget="BurntSushi.ripgrep.MSVC"),  # content search
        Package(brew="fzf", winget="junegunn.fzf"),  # fuzzy finder
        # system
        Package(brew="btop", scoop="btop-lhm"),  # monitoring
        Package(brew="fastfetch", winget="Fastfetch-cli.Fastfetch"),  # information
    ],
)
