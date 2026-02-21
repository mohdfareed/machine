"""Package manager bootstrap module.

Initializes and upgrades platform package managers (brew, apt, snap,
winget, scoop). Scripts are auto-discovered from ``scripts/`` and
filtered by platform suffix at runtime.

Auto-included by the tool for any module that declares packages.
"""

from machine.manifest import Module

module = Module()
