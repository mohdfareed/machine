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
        "core",
    ],
    files=[
        FileMapping(source="docker", target="~/homelab"),
        FileMapping(
            source="com.mc.backup.plist",
            target="~/Library/LaunchAgents/com.mc.backup.plist",
        ),
    ],
    packages=[
        *cask("tailscale"),
        # Dev tools
        *cask("docker", "dotnet-sdk", "powershell"),
        *brew("uv", "python", "go"),
        *brew("copilot-cli", "codex"),
        # Utilities
        *brew("mas", "fastfetch"),
        *brew("font-computer-modern", "font-jetbrains-mono-nerd-font"),
    ],
    env={
        "ICLOUD": "$HOME/Library/Mobile Documents/com~apple~CloudDocs",
        "MC_PRIVATE": "$ICLOUD/.machine",
    },
)
