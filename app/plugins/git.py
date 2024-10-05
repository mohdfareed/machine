"""Git plugin."""

from pathlib import Path
from typing import Annotated

import typer

from app import config, env, utils

app = typer.Typer(name="git", help="Git configuration setup.")


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

    environment = (
        env.Windows()
        if utils.WINDOWS
        else env.Unix() if utils.UNIX else env.Environment()
    )

    utils.LOGGER.info("Setting up git configuration...")
    utils.LOGGER.debug("global_gitconfig: %s", environment.GITCONFIG)
    utils.LOGGER.debug("global_gitignore: %s", environment.GITIGNORE)
    utils.LOGGER.debug("gitconfig: %s", gitconfig)
    utils.LOGGER.debug("gitignore: %s", gitignore)

    # utils.link(gitconfig, global_gitconfig)
    # utils.link(gitignore, global_gitignore)
    utils.LOGGER.debug("Git configuration setup complete")
