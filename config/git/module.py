"""Git configuration module."""

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

module = Module(
    files=[
        FileMapping(source=".gitconfig", target="~/.gitconfig"),
        FileMapping(source=".gitignore", target="~/.gitignore"),
        FileMapping(
            source=".gitconfig.win",
            target="~/.gitconfig.win",
            platforms=[Platform.WINDOWS],
        ),
    ],
    packages=[
        Package(name="git", brew="git", apt="git", winget="Git.Git"),
        Package(name="git-lfs", brew="git-lfs", apt="git-lfs", winget="GitHub.GitLFS"),
        Package(name="github-cli", brew="gh", apt="gh", winget="GitHub.cli"),
        Package(name="fork", cask="fork", winget="Fork.Fork"),
        (
            Package(
                name="lazygit",
                script="go install github.com/jesseduffield/lazygit@latest",
            )
            if PLATFORM == Platform.WSL
            else Package(
                name="lazygit",
                brew="lazygit",
                apt="lazygit",
                winget="JesseDuffield.lazygit",
            )
        ),
    ],
    overrides=[FileMapping(source=".gitconfig", target="~/.gitconfig.local")],
)
