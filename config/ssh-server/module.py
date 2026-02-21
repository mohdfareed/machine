"""SSH server setup module.

Scripts are auto-discovered from ``scripts/`` and filtered by platform
suffix at runtime.
"""

from machine.manifest import Module

module = Module(depends=["ssh"])
