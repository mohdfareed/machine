"""Personal laptop (macOS) machine manifest."""

from machine.manifest import MachineManifest, brew, cask, mas

manifest = MachineManifest(
    modules=[
        "git",
        "shell",
        "ssh",
        "vscode",
        "vscode-tunnel",
        "ghostty",
        "system",
    ],
    packages=[
        # Python
        *brew("python", "python-freethreading", "uv"),
        # PowerShell
        *cask("powershell"),
        # Fonts
        *brew("font-computer-modern", "font-jetbrains-mono-nerd-font"),
        # System
        *brew("fastfetch", "copilot-cli"),
        # Dev languages
        *brew("go", "shellcheck"),
        *cask("dotnet-sdk", "docker"),
        # Utilities
        *brew("mas", "gnu-time"),
        # Apps
        *cask("tailscale", "chatgpt"),
        *cask("iina", "mos", "monitorcontrol", "swish", "figma", "sf-symbols"),
        # Mac App Store
        *mas(Xcode=497799835, Craft=1487937127, Copilot=1447330651),
        *mas(Keynote=409183694, Numbers=409203825, Pages=409201541),
        *mas(Noir=1592917505, AdGuard=1440147259, Peek=1554235898),
    ],
    env={
        "MC_PRIVATE": "$ICLOUD/.machine/private",
        "ICLOUD": "$HOME/Library/Mobile Documents/com~apple~CloudDocs",
        "DEV": "$HOME/Developer",
        "DEV_BIN": "$DEV/bin",
        "GODOT": "/Applications/Godot_mono.app/Contents/MacOS/Godot",
    },
)
