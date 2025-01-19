"""Git plugin."""

__all__ = ["Git"]

from pathlib import Path
from typing import Protocol

import typer

from app import models, utils
from app.plugin import Plugin

from .pkg_managers import APT, Brew, Winget


class GitConfig(models.ConfigProtocol, Protocol):
    """Git configuration files."""

    gitconfig: Path
    gitignore: Path


class GitEnv(models.EnvProtocol, Protocol):
    """Git environment variables."""

    GITCONFIG: Path
    GITIGNORE: Path


class Git(Plugin[GitConfig, GitEnv]):
    """Configure git."""

    unix_packages = "git git-lfs gh"
    win_packages = "Git.Git GitHub.GitLFS GitHub.CLI Microsoft.GitCredentialManagerCore"

    def _setup(self) -> None:
        self.link()
        self.install()

    def link(self) -> None:
        """Link git configuration files."""
        utils.link(self.config.gitconfig, self.env.GITCONFIG)
        utils.link(self.config.gitignore, self.env.GITIGNORE)

    def install(self) -> None:
        """Install git."""
        if Brew.is_supported():
            Brew().install(self.unix_packages)
        elif APT.is_supported():
            self.linux_install(self.unix_packages)
        elif Winget.is_supported():
            Winget().install(self.win_packages)

        else:
            utils.LOGGER.error("No supported package manager found.")
            raise typer.Abort

    @staticmethod
    def linux_install(unix_packages: str) -> None:
        """Install git on a linux machine."""
        apt = APT()
        apt.add_keyring(
            "https://cli.github.com/packages/githubcli-archive-keyring.gpg",
            "https://cli.github.com/packages stable main",
            "github-cli",
        )
        apt.install(unix_packages)
