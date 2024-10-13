"""Setup functions for various tools and utilities."""

import shutil

import typer

from app import config, env, utils
from app.models import PluginException
from app.pkg_managers import APT, Brew, PackageManager, PIPx, Scoop, SnapStore, Winget
from app.utils import LOGGER

plugin_app = typer.Typer(name="shell", help="Configure shell.")
shell = utils.Shell()


def setup_fonts() -> None:
    """Setup fonts on a new machine."""
    LOGGER.info("Setting up tailscale...")
    PackageManager.from_spec(
        [
            (
                Brew,
                lambda: Brew().install(
                    "font-computer-modern font-jetbrains-mono-nerd-font"
                ),
            ),
            (APT, lambda: APT().install("fonts-jetbrains-mono fonts-lmodern")),
            (
                Scoop,
                lambda: Scoop()
                .add_bucket("nerd-fonts")
                .install("nerd-fonts/JetBrains-Mono"),
            ),
        ]
    )
    LOGGER.debug("Fonts were setup successfully.")


def setup_docker() -> None:
    """Setup docker on a new Debian machine."""
    LOGGER.info("Setting up Docker...")
    if utils.MACOS and utils.ARM:
        # REVIEW: check homebrew cask for apple silicon support
        LOGGER.warning("Docker is not supported on Apple Silicon.")
        LOGGER.warning("Download manually from: https://www.docker.com")

    elif utils.UNIX:
        utils.Shell().execute("curl -fsSL https://get.docker.com | sh")
    elif utils.WINDOWS:
        Winget().install("Docker.DockerDesktop")

    else:
        raise PluginException("Unsupported operating system")
    LOGGER.debug("Docker was setup successfully.")


def setup_python() -> None:
    """Setup python on a new Debian machine."""
    LOGGER.info("Setting up Python...")

    if Brew().is_supported():
        Brew().install("python pipx pyenv")

    if APT().is_supported():
        APT().install("python3 python3-pip python3-venv pipx")
        if not shutil.which("pyenv"):
            utils.Shell().execute("curl https://pyenv.run | bash")

    if Scoop().is_supported():
        # python is installed by default through winget
        Scoop().install("pipx pyenv")

    # install poetry
    PIPx().install("poetry")
    if utils.UNIX and shutil.which("poetry"):
        utils.Shell().execute(
            f"poetry completions zsh > {env.Unix().COMPLETIONS_PATH}/_poetry"
        )
    LOGGER.debug("Python was setup successfully.")


def setup_node() -> None:
    """Setup node on a new Debian machine."""
    LOGGER.info("Setting up Node...")

    if Brew().is_supported():
        Brew().install("nvm")
    if Winget().is_supported():
        Winget().install("Schniz.fnm")

    elif utils.LINUX and not shutil.which("nvm"):
        url = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh"
        utils.Shell().execute(f"curl -o- {url} | bash")

    else:  # only on unix systems can there be no package manager
        raise PluginException("Unsupported operating system")
    LOGGER.debug("Node was setup successfully.")


def setup_zed() -> None:
    """Setup the Zed text editor on a new machine."""
    LOGGER.info("Setting up Zed...")
    if utils.WINDOWS:
        raise PluginException("Zed is not supported on Windows.")

    if Brew().is_supported():
        Brew().install("zed")
    else:
        utils.Shell().execute("curl -f https://zed.dev/install.sh | sh")

    utils.link(config.Default().zed_settings, env.Unix().ZED_SETTINGS)
    LOGGER.debug("Zed was setup successfully.")


def install_btop() -> None:
    """Install btop on a machine."""
    if Brew().is_supported():
        Brew().install("btop")
    elif SnapStore().is_supported():
        SnapStore().install("btop")
    elif Scoop().is_supported():
        Scoop().install("btop-lhm")


def install_powershell(
    configuration: config.DefaultConfigArg = config.Default(),
) -> None:
    """Install PowerShell on a machine."""

    if Brew().is_supported():
        Brew().install("powershell", cask=True)
    elif Winget().is_supported():
        Winget().install("Microsoft.PowerShell")
    elif SnapStore().is_supported():
        SnapStore().install("powershell")
    utils.link(configuration.ps_profile, env.Windows().PS_PROFILE)


def install_nvim(
    configuration: config.DefaultConfigArg = config.Default(),
) -> None:
    """Install NeoVim on a machine."""

    if Brew().is_supported():
        Brew().install("nvim lazygit ripgrep fd")

    elif Winget().is_supported():
        Winget().install(
            "Neovim.Neovim JesseDuffield.lazygit BurntSushi.ripgrep sharkdp.fd"
        )

    elif SnapStore().is_supported():
        SnapStore().install("nvim lazygit-gm ")
        SnapStore().install("ripgrep", classic=True)
        APT().install("fd-find")

    utils.link(configuration.vim, env.Default().VIM)
    LOGGER.debug("Shell setup complete.")
