"""Git configuration module."""

from app.models import FileMapping, Module, Package, Platform

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
    overrides=[FileMapping(source=".gitconfig", target="~/.gitconfig.mc")],
    packages=[
        Package(name="git", brew="git", apt="git", winget="Git.Git"),
        Package(name="git-lfs", brew="git-lfs", apt="git-lfs", winget="GitHub.GitLFS"),
        Package(brew="lazygit", winget="JesseDuffield.lazygit"),
    ],
)
