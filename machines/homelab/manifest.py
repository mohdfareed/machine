"""Homelab (macOS) machine manifest."""

from machine.manifest import FileMapping, MachineManifest, Package, PkgManager

manifest = MachineManifest(
    pkg_managers=[PkgManager.BREW, PkgManager.MAS],
    modules=[
        "git",
        "shell",
        "ssh",
        "ssh-server",
        "vscode",
        "ghostty",
        "homelab",
        "system",
        "codex",
    ],
    files=[
        FileMapping(
            source="com.mc.backup.plist",
            target="~/Library/LaunchAgents/com.mc.backup.plist",
        ),
    ],
    packages=[
        Package(brew="go"),
        Package(brew="ffmpeg"),
    ],
)
