"""HomeLab (macOS) machine manifest."""

from machine.manifest import FileMapping, MachineManifest, Package

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
        FileMapping(source="CLAUDE.md", target="~/.claude/CLAUDE.md"),
        FileMapping(
            source="com.mc.backup.plist",
            target="~/Library/LaunchAgents/com.mc.backup.plist",
        ),
        FileMapping(
            source="com.mc.openclaw-env.plist",
            target="~/Library/LaunchAgents/com.mc.openclaw-env.plist",
        ),
        FileMapping(source="openclaw", target="~/.openclaw"),
    ],
    packages=[
        # OpenClaw (macOS app - node)
        Package(cask="openclaw"),
        # OpenClaw (CLI - gateway)
        Package(
            name="openclaw-cli",
            script="curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard",
        ),
        # Dev tools
        Package(brew="uv"),
        Package(brew="python"),
        Package(cask="powershell"),
        # Utilities
        Package(brew="mas"),
        Package(brew="fastfetch"),
        Package(cask="font-computer-modern"),
        Package(cask="font-jetbrains-mono-nerd-font"),
    ],
)
