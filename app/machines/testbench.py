"""Testing machine."""

__all__ = ["Test"]


from app import config, env, plugins
from app.machine import MachinePlugin
from app.models import PluginProtocol


class Test(MachinePlugin[config.Default, env.OSEnvType]):
    """Testbench machine."""

    @property
    def _config(self) -> config.Default:
        return config.Default()

    @property
    def _env(self) -> env.OSEnvType:
        return env.OSEnvironment()

    @property
    def plugins(self) -> list[type[PluginProtocol]]:
        return [plugins.Test]

    def setup(self) -> None:
        self.execute_setup()
