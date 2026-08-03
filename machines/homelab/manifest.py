"""HomeLab (macOS) machine manifest."""

from machine.manifest import FileMapping, MachineManifest, Package

manifest = MachineManifest(
    modules=[
        "git",
        "shell",
        "ssh",
        "ssh-server",
        "vscode",
        "ghostty",
        "homelab",
        "core",
        "codex",
    ],
    files=[
        FileMapping(
            source="com.mc.backup.plist",
            target="~/Library/LaunchAgents/com.mc.backup.plist",
        ),
    ],
    packages=[
        # Dev tools
        Package(brew="uv"),
        Package(brew="python"),
        Package(cask="powershell"),
        # Utilities
        Package(brew="mas"),
        Package(cask="font-computer-modern"),
        Package(cask="font-jetbrains-mono-nerd-font"),
    ],
)
