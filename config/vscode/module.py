"""VS Code configuration module."""

from pathlib import Path

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

match PLATFORM:
    case Platform.MACOS:
        _base = Path("~") / "Library" / "Application Support" / "Code" / "User"
    case Platform.WINDOWS:
        _base = Path(r"%APPDATA%") / "Code" / "User"
    case _:
        _base = Path("~/.config/Code/User")


module = Module(
    files=[
        FileMapping(source="snippets", target=str(_base / "snippets")),
        FileMapping(source="settings.json", target=str(_base / "settings.json")),
        FileMapping(source="keybindings.json", target=str(_base / "keybindings.json")),
        FileMapping(source="mcp.json", target=str(_base / "mcp.json")),
    ],
    packages=[
        Package(
            name="vscode",
            cask="visual-studio-code",
            apt="code",  # in Raspberry Pi OS repo
            winget="microsoft.VisualStudioCode",
            snap="code --classic",  # fallback: amd64-only,
        ),
    ],
)
