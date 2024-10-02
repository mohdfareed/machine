"""App utilities."""

import sys
from typing import Literal

SupportedShells = Literal["zsh", "bash", "pwsh", "powershell"]
"""Supported shells for commands execution."""

is_windows = sys.platform.startswith("win")
"""Check if the current platform is Windows."""
