"""Zed setup module."""

from pathlib import Path

from app import utils
from app.models import PluginException
from app.plugins.pkg_managers import Brew
from app.plugins.plugin import Configuration, Environment, Plugin, SetupFunc
from app.utils import LOGGER


class ZedConfig(Configuration):
    """Zed configuration files."""

    zed_settings: Path


class ZedEnv(Environment):
    """Zed environment variables."""

    ZED_SETTINGS: Path


class Zed(Plugin[ZedConfig, ZedEnv]):
    """Setup the Zed text editor on a new machine."""

    @property
    def plugin_setup(self) -> SetupFunc:
        return self._setup

    def _setup(self) -> None:
        LOGGER.info("Setting up Zed...")
        if utils.WINDOWS:
            raise PluginException("Zed is not supported on Windows.")

        if Brew().is_supported():
            Brew().install("zed")
        else:
            utils.Shell().execute("curl -f https://zed.dev/install.sh | sh")

        utils.link(self.config.zed_settings, self.env.ZED_SETTINGS)
        LOGGER.debug("Zed was setup successfully.")
