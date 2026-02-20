"""Git configuration module.

Deploys shared gitconfig (with ``[include]`` for platform and local
overrides) and a global gitignore. Installs git, git-lfs, and gh.

Platform scripts generate ``~/.gitconfig.platform`` with OS-specific
settings (credential helper, line-ending behavior on Windows).
"""

from machine.manifest import FileMapping, Module, Package

module = Module(
    files=[
        FileMapping(source="gitconfig", target="~/.gitconfig"),
        FileMapping(source="gitignore", target="~/.gitignore"),
    ],
    packages=[
        Package(name="git", brew="git", winget="Git.Git"),
        Package(name="gh", brew="gh", winget="GitHub.cli"),
        Package(name="git-lfs", brew="git-lfs", apt="git-lfs", winget="GitHub.GitLFS"),
    ],
    overrides={".gitconfig.local": "~/.gitconfig.local"},
)
