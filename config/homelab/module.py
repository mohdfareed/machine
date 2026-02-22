"""Homelab Docker service deployment module.

Provides the shared deploy script that symlinks compose files from the
machine's ``docker/`` directory into ``~/.homelab/``, provisions ``.env``
secrets, and runs ``docker compose up``.

Both the homelab Mac and the RPi include this module. Machine-specific
compose files stay under ``machines/<id>/docker/<service>/``.
"""

from machine.manifest import Module

module = Module()
