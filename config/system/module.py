"""System setup module.

Platform-specific OS configuration (package manager bootstrap, hostname,
SSH server, system defaults, etc.). Scripts are auto-discovered from
``scripts/`` and filtered by platform suffix at runtime.
"""

from machine.manifest import Module

module = Module()
