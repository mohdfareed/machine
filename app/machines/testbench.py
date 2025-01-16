"""Testing machine."""

__all__ = ["Test"]


from app import config, env, utils
from app.machine import MachinePlugin
from app.models import PluginProtocol
from app.plugins import Private

Environment = env.Unix if utils.UNIX else env.Windows


class Test(MachinePlugin[config.MachineConfig, env.MachineEnv]):
    """Testbench machine."""

    @property
    def plugins(self) -> list[type[PluginProtocol]]:
        return [
            Private,
        ]

    def __init__(self) -> None:
        self.config = config.MachineConfig()
        self.env = env.MachineEnv()
        super().__init__()

    @classmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""
        return True
