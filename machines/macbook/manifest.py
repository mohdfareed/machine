"""Personal laptop (macOS) machine manifest."""

from machine.manifest import MachineManifest, Package

manifest = MachineManifest(
    modules=[
        "git",
        "shell",
        "ssh",
        "vscode",
        "ghostty",
        "core",
        "zed",
        "raycast",
        "claude",
    ],
    files=[],
    packages=[
        # Dev languages
        Package(brew="uv"),
        Package(brew="python"),
        Package(brew="python-freethreading"),
        Package(brew="go"),
        Package(brew="shellcheck"),
        # NOTE: Docker Desktop cask ("docker") only delivers an Intel binary
        #   via Homebrew as of 2026-02. Install Docker Desktop manually on
        #   Apple Silicon until the cask ships a universal/ARM build.
        # Package(cask="docker"),
        Package(cask="powershell"),
        Package(cask="dotnet-sdk"),
        # Utilities
        Package(brew="mas"),
        Package(brew="gnu-time"),
        Package(brew="fastfetch"),
        Package(cask="copilot-cli"),
        Package(cask="codex"),
        Package(cask="font-computer-modern"),
        Package(cask="font-jetbrains-mono-nerd-font"),
        # Apps
        Package(cask="iina"),
        Package(cask="mos"),
        Package(cask="monitorcontrol"),
        Package(cask="swish"),
        Package(cask="tailscale"),
        Package(cask="craft"),
        Package(cask="chatgpt"),
        Package(cask="figma"),
        Package(cask="sf-symbols"),
        Package(cask="openclaw"),
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
