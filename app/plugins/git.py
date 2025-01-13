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


class GitEnv(models.EnvironmentProtocol, Protocol):
    """Git environment variables."""

    GITCONFIG: Path
    GITIGNORE: Path


class Git(Plugin[GitConfig, GitEnv]):
    """Configure git."""

    unix_packages = "git git-lfs gh"
    win_packages = "Git.Git GitHub.GitLFS GitHub.CLI Microsoft.GitCredentialManagerCore"

    def setup(self) -> None:
        """Set up git."""
        utils.LOGGER.info("Setting up git...")
        utils.link(self.config.gitconfig, self.env.GITCONFIG)
        utils.link(self.config.gitignore, self.env.GITIGNORE)

        if Brew.is_supported():
            Brew().install(self.unix_packages)
        elif APT.is_supported():
            self._linux_setup(self.unix_packages)
        elif Winget.is_supported():
            Winget().install(self.win_packages)
        else:
            utils.LOGGER.error("No supported package manager found.")
            raise typer.Abort
        utils.LOGGER.debug("Git setup complete")

    @staticmethod
    def _linux_setup(unix_packages: str) -> None:
        apt = APT()
        apt.add_keyring(
            "https://cli.github.com/packages/githubcli-archive-keyring.gpg",
            "https://cli.github.com/packages stable main",
            "github-cli",
        )
        apt.install(unix_packages)
