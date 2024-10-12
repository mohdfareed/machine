"""Git plugin."""

import typer

from app import config, env, utils

app = typer.Typer(name="git", help="Configure git.")


@app.command()
def setup(
    gitconfig: utils.ReqFileArg = config.Default().gitconfig,
    gitignore: utils.ReqFileArg = config.Default().gitignore,
    environment: env.EnvArg = env.Default(),
) -> None:
    """Configure git."""

    utils.LOGGER.info("Setting up git configuration...")
    utils.link(gitconfig, environment.GITCONFIG)
    utils.link(gitignore, environment.GITIGNORE)
    utils.LOGGER.debug("Git configuration setup complete")
