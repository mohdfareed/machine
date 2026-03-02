"""HomeLab (macOS) machine manifest."""

from machine.manifest import FileMapping, MachineManifest, Package, brew, cask

manifest = MachineManifest(
    modules=[
        "git",
        "shell",
        "ssh",
        "ssh-server",
        "vscode",
        "vsc-server",
        "ghostty",
        "homelab",
        "core",
    ],
    files=[
        FileMapping(
            source="com.mc.backup.plist",
            target="~/Library/LaunchAgents/com.mc.backup.plist",
        ),
        # OpenClaw gateway config (symlink entire dir so $include resolves)
        FileMapping(source="openclaw", target="~/.openclaw"),
    ],
    packages=[
        # OpenClaw (macOS app - node)
        *cask("openclaw"),
        # OpenClaw (CLI - gateway)
        Package(
            name="openclaw-cli",
            script="curl -fsSL https://openclaw.ai/install.sh | bash",
        ),
        # Dev tools
        *brew("uv", "python"),
        *cask("powershell"),
        # Utilities
        *brew("mas", "fastfetch"),
        *brew("font-computer-modern", "font-jetbrains-mono-nerd-font"),
    ],
)
