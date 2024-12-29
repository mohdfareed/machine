"""Testing machine."""

__all__ = ["Test"]

from pathlib import Path
from typing import Any

from app import env, models, utils
from app.machines.machine import Machine
from app.plugins import Plugin, Private, PrivateConfigData, SetupFunc

Environment = env.Unix if utils.UNIX else env.Windows


class TestConfig(PrivateConfigData):
    """Testing machine configuration files."""

    valid_field: Path = utils.create_temp_file("valid_field")
    invalid_field: int = 0


class Test(Machine[TestConfig, models.Environment]):
    """Testbench machine."""

    @property
    def plugins(self) -> list[Plugin[Any, Any]]:
        plugins: list[Plugin[Any, Any]] = [
            Private(TestConfig()),
        ]
        return plugins

    @property
    def machine_setup(self) -> SetupFunc:
        return self._setup

    def __init__(self) -> None:
        super().__init__(TestConfig(), Environment())

    @classmethod
    def is_supported(cls) -> bool:
        """Check if the plugin is supported."""
        return True

    def _setup(self) -> None:
        temp_dir = utils.create_temp_dir("private")
        (temp_dir / self.config.valid_field.name).touch()
        Private(TestConfig()).plugin_setup(private_dir=temp_dir)
