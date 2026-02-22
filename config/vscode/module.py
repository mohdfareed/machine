"""VS Code configuration module.

Deploys settings, keybindings, MCP config, snippets, and prompts.
Target directory is platform-aware.
"""

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

match PLATFORM:
    case Platform.MACOS:
        _base = "~/Library/Application Support/Code/User"
    case Platform.WINDOWS:
        _base = "%APPDATA%/Code/User"
    case _:
        _base = "~/.config/Code/User"

module = Module(
    files=[
        FileMapping(source=f"config/{name}", target=f"{_base}/{name}")
        for name in (
            "settings.json",
            "keybindings.json",
            "mcp.json",
            "snippets",
        )
    ],
    packages=[
        Package(
            name="visual-studio-code",
            brew="visual-studio-code --cask",
            winget="microsoft.VisualStudioCode",
        )
        if PLATFORM == Platform.MACOS
        else Package(
            name="visual-studio-code",
            apt="code",  # in Raspberry Pi OS repo
            winget="microsoft.VisualStudioCode",
            snap="code --classic",  # fallback: amd64-only,
        ),
    ],
)
