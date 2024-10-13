"""Shell setup module."""

import typer

from app import config, env, utils
from app.models import PluginException
from app.package_managers import APT, Brew, PackageManager
from app.utils import LOGGER

plugin_app_win = typer.Typer(name="shell", help="Configure shell.")
plugin_app = typer.Typer(name="shell", help="Configure shell.")
shell = utils.Shell()


@plugin_app.command()
def setup(
    configuration: config.DefaultConfigArg = config.Default(),
) -> None:
    """Setup the shell env.Unix() on a machine."""
    if utils.WINDOWS:
        raise PluginException("This command is not supported on Windows.")

    LOGGER.info("Setting up shell...")
    PackageManager.from_spec(
        [
            (Brew, lambda: Brew().install("zsh tmux eza bat")),
            (APT, lambda: APT().install("zsh tmux bat eza")),
        ]
    )

    # symlink config files
    env.Unix().ZSHENV.unlink(missing_ok=True)
    configuration.zshenv.link_to(env.Unix().ZSHENV)
    env.Unix().ZSHRC.unlink(missing_ok=True)
    configuration.zshrc.link_to(env.Unix().ZSHRC)
    env.Unix().TMUX_CONFIG.unlink(missing_ok=True)
    configuration.tmux_config.link_to(env.Unix().TMUX_CONFIG)

    # update zinit and its plugins
    LOGGER.info("Updating zinit and its plugins...")
    source_env = f"source {configuration.zshenv} && source {configuration.zshrc}"
    shell.execute(f"{source_env} && zinit self-update && zinit update")

    # clean up
    shell.execute("sudo rm -rf ~/.zcompdump*", throws=False)
    shell.execute("sudo rm -rf ~/.zshrc", throws=False)
    shell.execute("sudo rm -rf ~/.zsh_sessions", throws=False)
    shell.execute("sudo rm -rf ~/.zsh_history", throws=False)
    shell.execute("sudo rm -rf ~/.lesshst", throws=False)
    LOGGER.debug("Shell setup complete.")
