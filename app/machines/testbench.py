"""Testing machine."""

__all__ = ["Test"]

from pathlib import Path
from typing import Any

from app import config, env, utils
from app.machines.machine import Machine
from app.plugins import Plugin, Private

Environment = env.Unix if utils.UNIX else env.Windows


class TestConfig(config.Private):
    """Testing machine configuration files."""

    valid_field: Path = utils.create_temp_file("valid_field")
    invalid_field: int = 0


class Test(Machine[TestConfig, None]):
    """Testbench machine."""

    @property
    def plugins(self) -> list[Plugin[Any, Any]]:
        plugins: list[Plugin[Any, Any]] = [
            Private(TestConfig()),
        ]
        return plugins

    def __init__(self) -> None:
        super().__init__(TestConfig(), None)

    @classmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""
        return True
