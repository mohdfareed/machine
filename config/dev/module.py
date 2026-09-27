"""Development runtimes, agents, and desktop editors."""

import os
from pathlib import Path

from app.env import PLATFORM
from app.models import FileMapping, Module, Package, Platform

_vscode = Path("~") / "Library" / "Application Support" / "Code" / "User"
_zed = Path("~") / ".config" / "zed"

if PLATFORM == Platform.WIN:
    _vscode = Path(os.environ["APPDATA"]) / "Code" / "User"
    _zed = Path(os.environ["APPDATA"]) / "Zed"

module = Module(
    files=[
        # VS Code
        FileMapping(
            source="vscode/snippets",
            target=_vscode / "snippets",
            platforms=[Platform.MAC, Platform.WIN],
        ),
        FileMapping(
            source="vscode/settings.json",
            target=_vscode / "settings.json",
            platforms=[Platform.MAC, Platform.WIN],
        ),
        FileMapping(
            source="vscode/keybindings.json",
            target=_vscode / "keybindings.json",
            platforms=[Platform.MAC, Platform.WIN],
        ),
        FileMapping(
            source="vscode/mcp.json",
            target=_vscode / "mcp.json",
            platforms=[Platform.MAC, Platform.WIN],
        ),
        # Zed
        FileMapping(
            source="zed/keymap.json",
            target=_zed / "keymap.json",
            platforms=[Platform.MAC, Platform.WIN],
        ),
        FileMapping(
            source="zed/settings.json",
            target=_zed / "settings.json",
            platforms=[Platform.MAC, Platform.WIN],
        ),
        FileMapping(
            source="zed/snippets.json",
            target=_zed / "snippets" / "snippets.json",
            platforms=[Platform.MAC, Platform.WIN],
        ),
        FileMapping(
            source="zed/tasks.json",
            target=_zed / "tasks.json",
            platforms=[Platform.MAC, Platform.WIN],
        ),
    ],
    packages=[
        Package(name="python", brew="python", winget="Python.Python.3.14"),
        Package(brew="python-freethreading"),
        Package(name="go", brew="go", winget="golang.Go"),
        Package(name="dotnet", cask="dotnet-sdk", winget="Microsoft.DotNet.SDK.10"),
        Package(name="codex", cask="codex", winget="OpenAI.Codex"),
        Package(
            name="vscode",
            cask="visual-studio-code",
            winget="microsoft.VisualStudioCode",
            platforms=[Platform.MAC, Platform.WIN],
        ),
        Package(
            cask="zed",
            winget="ZedIndustries.Zed",
            platforms=[Platform.MAC, Platform.WIN],
        ),
        # Extension dependencies.
        Package(
            brew="shellcheck",
            winget="koalaman.shellcheck",
            platforms=[Platform.MAC, Platform.WIN],
        ),
    ],
)
