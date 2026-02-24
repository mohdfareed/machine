"""HomeLab (macOS) machine manifest."""

from machine.manifest import FileMapping, MachineManifest, brew, cask

manifest = MachineManifest(
    modules=[
        "git",
        "shell",
        "ssh",
        "ssh-server",
        "vscode",
        "vsc-tunnel",
        "ghostty",
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
        *cask("dotnet-sdk", "powershell"),
        *brew("uv", "python", "go"),
        *brew("copilot-cli", "codex"),
        # Utilities
        *brew("mas", "fastfetch"),
        *brew("font-computer-modern", "font-jetbrains-mono-nerd-font"),
    ],
    env={
        "MC_ENV_FILES": "homelab tailscale agents",
        "ICLOUD": "$HOME/Library/Mobile Documents/com~apple~CloudDocs",
        "MC_PRIVATE": "$ICLOUD/.machine",
    },
)
