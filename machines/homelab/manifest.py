"""HomeLab (macOS) machine manifest."""

from machine.manifest import FileMapping, MachineManifest, brew, cask, mas

manifest = MachineManifest(
    modules=[
        "git",
        "shell",
        "ssh",
        "ssh-server",
        "vscode",
        "vsc-server",
        "ghostty",
        "openclaw",
        "homelab",
        "core",
    ],
    files=[
        FileMapping(
            source="com.mc.backup.plist",
            target="~/Library/LaunchAgents/com.mc.backup.plist",
        ),
    ],
    packages=[
        # Dev tools
        *brew("uv", "python"),
        *cask("powershell"),
        # Utilities
        *brew("mas", "fastfetch"),
        *brew("font-computer-modern", "font-jetbrains-mono-nerd-font"),
        # Mac App Store
        *mas(Peek=1554235898),
    ],
)
