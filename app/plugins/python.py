"""Python setup module."""

__all__ = ["Python"]

import shutil
from pathlib import Path
from typing import Protocol

from app import models, utils
from app.plugins.pkg_managers import APT, Brew, PIPx, Scoop
from app.plugins.plugin import Plugin
from app.utils import LOGGER


class PythonEnv(models.EnvironmentProtocol, Protocol):
    """Python environment variables."""

    COMPLETIONS_PATH: Path


class Python(Plugin[None, PythonEnv]):
    """Setup Python on a new machine."""

    def __init__(self, env: PythonEnv) -> None:
        super().__init__(None, env)

    def setup(self) -> None:
        LOGGER.info("Setting up Python...")

        if Brew.is_supported():
            Brew().install("python pipx pyenv")
        elif APT.is_supported():
            APT().install("python3 python3-pip python3-venv pipx")
            if not shutil.which("pyenv"):
                utils.Shell().execute("curl https://pyenv.run | bash")
        elif Scoop.is_supported():
            Scoop().install("pipx pyenv")

        PIPx().install("poetry")
        if utils.UNIX and shutil.which("poetry"):
            utils.Shell().execute(
                f"poetry completions zsh > {self.env.COMPLETIONS_PATH}/_poetry"
            )
        LOGGER.debug("Python was setup successfully.")
