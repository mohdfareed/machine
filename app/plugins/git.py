"""Git plugin."""

import typer

from app import config, env, utils
from app.pkg_managers import APT, Brew, PackageManager, Winget

plugin_app = typer.Typer(name="git", help="Configure git.")


@plugin_app.command()
def setup(
    configuration: config.DefaultConfigArg = config.Default(),
) -> None:
    """Configure git."""

    utils.LOGGER.info("Setting up git configuration...")
    utils.link(configuration.gitconfig, env.Default().GITCONFIG)
    utils.link(configuration.gitignore, env.Default().GITIGNORE)
    utils.LOGGER.debug("Git configuration setup complete")


@plugin_app.command()
def install() -> None:
    """Install git."""

    def _linux_setup() -> None:
        apt = APT()
        apt.install("git git-lfs")
        apt.add_keyring(
            "https://cli.github.com/packages/githubcli-archive-keyring.gpg",
            "https://cli.github.com/packages stable main",
            "github-cli",
        )
        apt.update()
        apt.install("gh")

    PackageManager.from_spec(
        [
            (Brew, lambda: Brew().install("git git-lfs gh")),
            (APT, _linux_setup),
            (
                Winget,
                lambda: Winget().install(
                    "Git.Git GitHub.GitLFS GitHub.CLI Microsoft.GitCredentialManagerCore"
                ),
            ),
        ]
    )
