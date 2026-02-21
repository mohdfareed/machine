"""Personal laptop (macOS) machine manifest."""

from machine.manifest import MachineManifest, brew, cask

manifest = MachineManifest(
    modules=[
        "git",
        "shell",
        "ssh",
        "ssh-server",
        "vscode",
        "vscode-tunnel",
        "ghostty",
        "system",
    ],
    packages=[
        *cask("tailscale"),
        # Dev tools
        *cask("uv", "docker"),
        *brew("python", "go", "dotnet-sdk", "powershell"),
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
