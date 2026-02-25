"""Git configuration module.

Deploys shared gitconfig (with ``[include]`` for platform and local
overrides) and a global gitignore. Installs git, git-lfs, and gh.
"""

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

module = Module(
    files=(
        [
            FileMapping(source=".gitconfig", target="~/.gitconfig"),
            FileMapping(source=".gitignore", target="~/.gitignore"),
        ]
        if PLATFORM != Platform.WINDOWS
        else [
            FileMapping(source=".gitconfig", target="~/.gitconfig"),
            FileMapping(source=".gitignore", target="~/.gitignore"),
            FileMapping(source=".gitconfig.win", target="~/.gitconfig.win"),
        ]
    ),
    packages=[
        Package(
            name="git",
            brew="git gh git-lfs",
            apt="git gh git-lfs",
            winget="Git.Git GitHub.cli GitHub.GitLFS",
        ),
    ],
    overrides=[FileMapping(source=".gitconfig", target="~/.gitconfig.local")],
)
