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
        "homelab",
        "core",
    ],
    files=[
        FileMapping(
            source="com.mc.backup.plist",
            target="~/Library/LaunchAgents/com.mc.backup.plist",
        ),
        # OpenClaw gateway config (symlinked to ~/.openclaw/)
        FileMapping(source="openclaw/openclaw.json", target="~/.openclaw/openclaw.json"),
        FileMapping(source="openclaw/config", target="~/.openclaw/config"),
        FileMapping(source="openclaw/workspace", target="~/.openclaw/workspace"),
        FileMapping(source="openclaw/cron", target="~/.openclaw/cron"),
    ],
    packages=[
        # OpenClaw (macOS app — gateway + CLI + node)
        *cask("openclaw"),
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
