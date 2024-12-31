"""Git plugin."""

__all__ = ["Git", "GitConfig", "GitEnv"]

from pathlib import Path

from app import models, utils

from .pkg_managers import APT, Brew, Winget
from .plugin import Plugin, SetupFunc


class GitConfig(models.ConfigFiles):
    """Git configuration files."""

    gitconfig: Path
    gitignore: Path


class GitEnv(models.Environment):
    """Git environment variables."""

    GITCONFIG: Path
    GITIGNORE: Path


class Git(Plugin[GitConfig, GitEnv]):
    """Configure git."""

    unix_packages = "git git-lfs gh"
    win_packages = "Git.Git GitHub.GitLFS GitHub.CLI Microsoft.GitCredentialManagerCore"

    @property
    def plugin_setup(self) -> SetupFunc:
        return self._setup

    def _setup(self) -> None:
        utils.LOGGER.info("Setting up git...")
        utils.link(self.config.gitconfig, self.env.GITCONFIG)
        utils.link(self.config.gitignore, self.env.GITIGNORE)

        utils.install_from_specs(
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
