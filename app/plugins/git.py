"""Git plugin."""

from pathlib import Path
from typing import Annotated

from app import config, env, utils


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
