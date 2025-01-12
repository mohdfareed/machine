"""Git plugin."""

__all__ = ["Git"]

from pathlib import Path
from typing import Protocol

from app import models, utils

from .pkg_managers import APT, Brew, Winget, install_from_specs
from .plugin import Plugin


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

        install_from_specs(
            [
                (Brew, lambda: Brew().install(self.unix_packages)),
                (APT, lambda: self._linux_setup(self.unix_packages)),
                (Winget, lambda: Winget().install(self.win_packages)),
            ]
        )
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
