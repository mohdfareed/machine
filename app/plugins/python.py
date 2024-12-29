"""Python setup module."""

import shutil

from app import env, utils
from app.plugins.pkg_managers import APT, Brew, PIPx, Scoop
from app.plugins.plugin import Environment, Plugin, SetupFunc
from app.utils import LOGGER


class PythonEnv(Environment):
    """Python environment variables."""

    COMPLETIONS_PATH: str


class Python(Plugin[None, PythonEnv]):
    """Setup Python on a new machine."""

    @property
    def plugin_setup(self) -> SetupFunc:
        return self._setup

    def __init__(self) -> None:
        super().__init__(None, PythonEnv())

    def _setup(self) -> None:
        LOGGER.info("Setting up Python...")

        if Brew().is_supported():
            Brew().install("python pipx pyenv")

        if APT().is_supported():
            APT().install("python3 python3-pip python3-venv pipx")
            if not shutil.which("pyenv"):
                utils.Shell().execute("curl https://pyenv.run | bash")

        if Scoop().is_supported():
            Scoop().install("pipx pyenv")

        PIPx().install("poetry")
        if utils.UNIX and shutil.which("poetry"):
            utils.Shell().execute(
                f"poetry completions zsh > {env.Unix().COMPLETIONS_PATH}/_poetry"
            )
        LOGGER.debug("Python was setup successfully.")
