"""SSH module.

Provisions SSH keys from a private store (``MC_PRIVATE``) and deploys a
shared SSH config. Also installs and enables the SSH server on each
platform. All scripts are auto-discovered from ``scripts/``.
"""

from machine.manifest import FileMapping, Module

module = Module(
    files=[
        FileMapping(source="ssh.config", target="~/.ssh/config"),
    ],
)
