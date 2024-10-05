"""Git plugin."""

from pathlib import Path
from typing import Annotated

import typer

from app import config, env, utils

app = typer.Typer(name="git", help="Git configuration setup.")

_global_gitconfig = Path.home() / ".gitconfig"
_global_gitignore = Path.home() / ".gitignore"


@app.command()
def setup(
    gitconfig: Annotated[
        Path,
        typer.Argument(
            help="Path to the .gitconfig file.",
            callback=utils.validate(utils.path_exists, utils.is_file),
        ),
    ] = config.Default().gitconfig,
    gitignore: Annotated[
        Path,
        typer.Argument(
            help="Path to the .gitignore file.",
            callback=utils.validate(utils.path_exists, utils.is_file),
        ),
    ] = config.Default().gitignore,
) -> None:
    """Configure git."""

    if utils.WINDOWS:
        global_gitconfig = env.Windows().USERPROFILE / ".gitconfig"
        global_gitignore = env.Windows().USERPROFILE / ".gitignore"
    if utils.LINUX or utils.MACOS:
        global_gitconfig = env.Unix().XDG_CONFIG_HOME / "git" / "config"
        global_gitignore = env.Unix().XDG_CONFIG_HOME / "git" / "ignore"
    else:
        global_gitconfig = _global_gitconfig
        global_gitignore = _global_gitignore

    utils.LOGGER.info("Setting up git configuration...")
    utils.LOGGER.debug("global_gitconfig: %s", global_gitconfig)
    utils.LOGGER.debug("global_gitignore: %s", global_gitignore)
    utils.LOGGER.debug("gitconfig: %s", gitconfig)
    utils.LOGGER.debug("gitignore: %s", gitignore)

    # utils.link(gitconfig, global_gitconfig)
    # utils.link(gitignore, global_gitignore)
    # utils.LOGGER.debug("Git configuration setup complete")
