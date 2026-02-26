"""Personal laptop (macOS) machine manifest."""

from machine.manifest import MachineManifest, brew, cask, mas

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "vscode", "ghostty", "core"],
    files=[],
    packages=[
        *cask("openclaw"),
        # Dev languages
        *brew("uv", "python", "python-freethreading"),
        *brew("go", "shellcheck"),
        *cask("powershell", "dotnet-sdk"),
        # NOTE: Docker Desktop cask ("docker") only delivers an Intel binary via
        # Homebrew as of 2026-02. Install Docker Desktop manually on Apple Silicon
        # until the cask ships a universal/ARM build.
        # *cask("docker"),
        # Utilities
        *brew("mas", "gnu-time", "fastfetch"),
        *brew("copilot-cli", "codex"),
        *brew("font-computer-modern", "font-jetbrains-mono-nerd-font"),
        # Apps
        *cask("iina", "mos", "monitorcontrol", "swish"),
        *cask("tailscale", "chatgpt", "figma", "sf-symbols"),
        # Mac App Store
        *mas(Xcode=497799835, Craft=1487937127, Copilot=1447330651),
        *mas(Keynote=409183694, Numbers=409203825, Pages=409201541),
        *mas(Noir=1592917505, AdGuard=1440147259, Peek=1554235898),
    ],
    env={
        "ICLOUD": "$HOME/Library/Mobile Documents/com~apple~CloudDocs",
        "MC_HOSTNAME": "mohds-macbook",
        "MC_ENV_FILES": "agents tailscale misc",
        "MC_PRIVATE": "$ICLOUD/.machine",
    },
)
