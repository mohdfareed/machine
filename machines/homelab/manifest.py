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
        Package(name="openclaw", cask="openclaw"),
        # OpenClaw (CLI - gateway)
        Package(
            name="openclaw-cli",
            script="curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard",
        ),
        # Dev tools
        *[Package(name=name, brew=name) for name in ("uv", "python")],
        Package(name="powershell", cask="powershell"),
        # Utilities
        *[Package(name=name, brew=name) for name in ("mas", "fastfetch", "font-computer-modern")],
        Package(name="font-jetbrains-mono-nerd-font", brew="font-jetbrains-mono-nerd-font"),
    ],
)
