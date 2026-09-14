"""Homelab (macOS) machine manifest."""

from app.models import FileMapping, Machine, Package, PkgManager

manifest = Machine(
    pkg_managers=[PkgManager.BREW, PkgManager.MAS],
    modules=[
        "system",
        "homelab",
        "terminal.git",
        "terminal.shell",
        "terminal.ssh",
        "terminal.emulators",
        "development.python",
        "development.agents",
        "development.vscode",
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
