"""Testing machine."""

__all__ = ["Test"]

from typing import Any

from app import config, env, utils
from app.machine import MachinePlugin
from app.plugin import Plugin
from app.plugins import Private

Environment = env.Unix if utils.UNIX else env.Windows


class Test(MachinePlugin[config.MachineConfig, env.MachineEnv]):
    """Testbench machine."""

    @property
    def plugins(self) -> list[type[Plugin[Any, Any]]]:
        return [
            Private,
        ]

    def __init__(self) -> None:
        super().__init__(config.MachineConfig(), Environment())

    @classmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""
        return True
