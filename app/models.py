"""App models."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from app import utils

T = TypeVar("T", bound="BaseEnvironment")


class BaseConfig(BaseModel, ABC):
    """Configuration files."""


class BaseEnvironment(BaseSettings, ABC):
    """Environment variables."""

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    @abstractmethod
    def load(self: T, env: Path) -> T:
        """Load environment variables from a file."""

        utils.LOGGER.debug("Loaded environment variables from: %s", env)
        env_vars = utils.load_env(env)
        for field in self.model_fields:
            if field in env_vars:
                setattr(self, field, env_vars[field])
        return self
