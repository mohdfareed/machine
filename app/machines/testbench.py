"""Testing machine."""

__all__ = ["Test"]


from app import config, env, plugins
from app.machine import MachinePlugin
from app.models import PluginProtocol


class Test(MachinePlugin[config.MachineConfig, env.OSEnvType]):
    """Testbench machine."""

    @property
    def _config(self) -> config.MachineConfig:
        return config.MachineConfig()

    @property
    def _env(self) -> env.OSEnvType:
        return env.OSEnvironment()

    @property
    def plugins(self) -> list[type[PluginProtocol]]:
        return [plugins.Test]
