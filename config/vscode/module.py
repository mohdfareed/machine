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
        FileMapping(source=f"config/{name}", target=str(_base / name))
        for name in (
            "settings.json",
            "keybindings.json",
            "mcp.json",
            "snippets",
        )
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
