"""Personal laptop (macOS) machine manifest."""

from machine.manifest import MachineManifest, Package, PkgManager

manifest = MachineManifest(
    pkg_managers=[PkgManager.BREW, PkgManager.MAS],
    modules=[
        "git",
        "shell",
        "ssh",
        "vscode",
        "ghostty",
        "system",
        "zed",
        "raycast",
        "codex",
    ],
    files=[],
    packages=[
        # Dev languages
        Package(brew="go"),
        Package(brew="shellcheck"),
        Package(cask="docker-desktop"),
        Package(cask="dotnet-sdk"),
        # Utilities
        Package(brew="gnu-time"),
        Package(cask="copilot-cli"),
        Package(cask="font-computer-modern"),
        # Apps
        Package(cask="iina"),
        Package(cask="mos"),
        Package(cask="monitorcontrol"),
        Package(cask="swish"),
        Package(cask="tailscale"),
        Package(cask="craft"),
        Package(cask="figma"),
        Package(cask="sf-symbols"),
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
