"""Git plugin."""

from pathlib import Path
from typing import Annotated

import typer

from app import config, env, utils

app = typer.Typer(name="git", help="Configure git.")


@app.command()
def setup(
    gitconfig: Path = config.Default().gitconfig,
    gitignore: Path = config.Default().gitignore,
    environment: Annotated[env.Environment, utils.InternalArg] = env.Default(),
) -> None:
    """Configure git."""

    utils.LOGGER.info("Setting up git configuration...")
    utils.link(gitconfig, environment.GITCONFIG)
    utils.link(gitignore, environment.GITIGNORE)
    utils.LOGGER.debug("Git configuration setup complete")
