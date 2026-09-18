"""VSCode configuration module."""

from pathlib import Path

from app.env import PLATFORM
from app.models import FileMapping, Module, Package, Platform

match PLATFORM:
    case Platform.MAC:
        _base = Path("~") / "Library" / "Application Support" / "Code" / "User"
    case Platform.WIN:
        _base = Path(r"%APPDATA%") / "Code" / "User"
    case _:
        _base = Path("~/.config/Code/User")


module = Module(
    files=[
        FileMapping(source="snippets", target=_base / "snippets"),
        FileMapping(source="settings.json", target=_base / "settings.json"),
        FileMapping(source="keybindings.json", target=_base / "keybindings.json"),
        FileMapping(source="mcp.json", target=_base / "mcp.json"),
    ],
    packages=[
        Package(
            name="vscode",
            cask="visual-studio-code",
            apt="code",  # in Raspberry Pi OS repo
            winget="microsoft.VisualStudioCode",
            snap="code",  # fallback: amd64-only,
            snap_classic=True,
        ),
    ],
)
