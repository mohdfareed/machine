"""Homelab (macOS) machine manifest."""

from app.machine import FileMapping, Machine, Package, PkgManager

manifest = Machine(
    pkg_managers=[PkgManager.BREW, PkgManager.MAS],
    modules=[
        "git",
        "shell",
        "ssh",
        "ssh-server",
        "vscode",
        "terminal",
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
