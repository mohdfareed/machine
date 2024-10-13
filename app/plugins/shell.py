"""Setup module containing a `setup` function for setting up the shell on a new machine."""

import typer

from app import config, env, utils
from app.plugins.package_managers import APT, Brew, PackageManager, Winget
from app.utils import LOGGER

plugin_app_win = typer.Typer(name="shell", help="Configure shell.")
plugin_app = typer.Typer(name="shell", help="Configure shell.")
shell = utils.Shell()


@plugin_app.command()
def setup(
    configuration: config.DefaultConfigArg = config.Default(),
    environment: env.UnixEnvArg = env.Unix(),
) -> None:
    """Setup the shell environment on a machine."""
    LOGGER.info("Setting up shell...")

    PackageManager.from_spec(
        [
            (Brew, lambda: Brew().install("zsh powershell tmux eza bat")),
            (APT, lambda: APT().install("zsh tmux bat eza")),
        ]
    )

    # symlink config files
    environment.ZSHENV.unlink(missing_ok=True)
    configuration.zshenv.link_to(environment.ZSHENV)
    environment.ZSHRC.unlink(missing_ok=True)
    configuration.zshrc.link_to(environment.ZSHRC)
    environment.TMUX_CONFIG.unlink(missing_ok=True)
    configuration.tmux_config.link_to(environment.TMUX_CONFIG)

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


@plugin_app_win.command()
def setup_win(
    configuration: config.WindowsConfigArg = config.Windows(),
    environment: env.WinEnvArg = env.Windows(),
) -> None:
    """Setup the shell environment on a Windows machine."""
    LOGGER.info("Setting up shell...")
    Winget().install("Microsoft.PowerShell")

    environment.PS_PROFILE.unlink(missing_ok=True)
    configuration.ps_profile.link_to(environment.PS_PROFILE)
    environment.VIM.unlink(missing_ok=True)
    configuration.vim.link_to(environment.VIM)
    LOGGER.debug("Shell setup complete.")
