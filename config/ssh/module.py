"""SSH client module.

Provisions SSH keys from a private store (``MC_PRIVATE``) and deploys a
shared SSH client config. Skips key provisioning if ``MC_PRIVATE`` is unset.
All scripts are auto-discovered from ``scripts/``.
"""

from machine.manifest import FileMapping, Module

module = Module(
    files=[
        FileMapping(source="ssh.config", target="~/.ssh/config"),
    ],
)
