"""HomeLab (macOS) machine manifest."""

from machine.manifest import MachineManifest, brew, cask

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
