"""Git configuration module."""

from app.models import FileMapping, Module, Package, Platform

module = Module(
    files=[
        FileMapping(source=".gitconfig", target="~/.gitconfig"),
        FileMapping(source=".gitignore", target="~/.gitignore"),
        FileMapping(
            source=".gitconfig.win", target="~/.config/git/config.win", platforms=[Platform.WIN]
        ),
    ],
    overrides=[
        FileMapping(source=".gitconfig", target="~/.config/git/config.mc"),
    ],
    packages=[
        Package(name="git", brew="git", apt="git", winget="Git.Git"),
        Package(name="git-lfs", brew="git-lfs", apt="git-lfs", winget="GitHub.GitLFS"),
    ],
)
