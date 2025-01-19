"""The machine setup package."""

__all__ = ["APP_NAME", "__version__"]

from importlib.metadata import version

APP_NAME = "machine-setup"
__version__ = version("machine")
