"""Application settings and global configuration."""

import logging
from importlib.metadata import metadata
from pathlib import Path
from typing import ClassVar

from pydantic import computed_field

from .base import BaseAppSettings

_meta = metadata("machine")


class AppSettings(BaseAppSettings):
    name: ClassVar[str] = _meta["Name"]
    version: ClassVar[str] = _meta["Version"]
    description: ClassVar[str] = _meta["Summary"]

    logger: ClassVar[logging.Logger] = logging.getLogger(name + ".config")

    debug: bool = False
    dry_run: bool = False
    home: Path = Path.home() / ".machine"

    @computed_field
    @property
    def logs_path(self) -> Path:
        """Path to log directory."""
        return self.home / "logs"


app_settings = AppSettings()
"""Application settings singleton."""
