"""Core system setup module.

Platform-specific OS configuration (hostname, system defaults, Touch ID,
file sharing, Windows features, etc.). Scripts are auto-discovered from
``scripts/`` and filtered by platform suffix at runtime.
"""

from machine.manifest import Module

module = Module()
