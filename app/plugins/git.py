"""Git plugin."""

from pathlib import Path
from typing import Annotated

import typer

from app import config, env, utils

GitConfigArg = Annotated[
    Path,
    typer.Argument(
        help="Path to the .gitconfig file.",
        callback=utils.validate(utils.is_file),
    ),
]
GitIgnoreArg = Annotated[
    Path,
    typer.Argument(
        help="Path to the .gitignore file.",
        callback=utils.validate(utils.is_file),
    ),
]
app = typer.Typer(name="git", help="Git configuration setup.")


@app.command()
def setup(
    gitconfig: GitConfigArg = config.Default().gitconfig,
    gitignore: GitIgnoreArg = config.Default().gitignore,
    environment: env.EnvArg = env.OSEnv(),
) -> None:
    """Configure git."""

    utils.LOGGER.info("Setting up git configuration...")
    utils.LOGGER.debug("global_gitconfig: %s", environment.GITCONFIG)
    utils.LOGGER.debug("global_gitignore: %s", environment.GITIGNORE)
    utils.LOGGER.debug("gitconfig: %s", gitconfig)
    utils.LOGGER.debug("gitignore: %s", gitignore)

    utils.link(gitconfig, environment.GITCONFIG)
    utils.link(gitignore, environment.GITIGNORE)
    utils.LOGGER.debug("Git configuration setup complete")
