"""Testing machine."""

__all__ = ["Test"]


from app import config, env
from app.plugin import Plugin


class Test(Plugin[config.MachineConfig, env.MachineEnv]):
    """Testbench plugin."""

    def _setup(self) -> None: ...
