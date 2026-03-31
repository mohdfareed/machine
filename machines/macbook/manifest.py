"""Personal laptop (macOS) machine manifest."""

from machine.manifest import MachineManifest, Package

manifest = MachineManifest(
    modules=["git", "shell", "ssh", "vscode", "ghostty", "core", "zed", "raycast"],
    files=[],
    packages=[
        # Dev languages
        *[
            Package(name=name, brew=name)
            for name in (
                "uv",
                "python",
                "python-freethreading",
                "go",
                "shellcheck",
            )
        ],
        # NOTE: Docker Desktop cask ("docker") only delivers an Intel binary
        #   via Homebrew as of 2026-02. Install Docker Desktop manually on
        #   Apple Silicon until the cask ships a universal/ARM build.
        # Package(name="docker", cask="docker"),
        *[Package(name=name, cask=name) for name in ("powershell", "dotnet-sdk")],
        # Utilities
        *[Package(name=name, brew=name) for name in ("mas", "gnu-time", "fastfetch")],
        *[
            Package(name=name, cask=name)
            for name in (
                "copilot-cli",
                "codex",
                "font-computer-modern",
                "font-jetbrains-mono-nerd-font",
            )
        ],
        # Apps
        *[
            Package(name=name, cask=name)
            for name in (
                "iina",
                "mos",
                "monitorcontrol",
                "swish",
                "tailscale",
                "craft",
                "chatgpt",
                "figma",
                "sf-symbols",
                "openclaw",
            )
        ],
        # Mac App Store
        Package(name="Xcode", mas=497799835),
        Package(name="Copilot", mas=1447330651),
        Package(name="Keynote", mas=409183694),
        Package(name="Numbers", mas=409203825),
        Package(name="Pages", mas=409201541),
        Package(name="Noir", mas=1592917505),
        Package(name="AdGuard", mas=1440147259),
        Package(name="Peek", mas=1554235898),
    ],
)
