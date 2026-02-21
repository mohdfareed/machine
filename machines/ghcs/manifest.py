"""GitHub Codespaces machine manifest."""

from machine.manifest import MachineManifest

manifest = MachineManifest(
    modules=["git", "shell"],
)
