"""App utilities."""

import sys

WINDOWS = "win" in sys.platform
"""Whether the current platform is Windows."""

MACOS = sys.platform == "darwin"
"""Whether the current platform is macOS."""

LINUX = "linux" in sys.platform
"""Whether the current platform is Linux."""

ARM = "arm" in sys.platform
"""Whether the current platform is ARM-based."""
