"""Claude and Claude Code CLI configuration module."""

from pathlib import Path

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

match PLATFORM:
    case Platform.WINDOWS:
        _claude_desktop = Path("%APPDATA%") / "Claude"
    case Platform.MACOS:
        _claude_desktop = Path("~/Library/Application Support/Claude")
    case _:  # linux
        _claude_desktop = Path("~/.config/Claude")

module = Module(
    files=[
        FileMapping(source="settings.json", target=str(Path("~/.claude/settings.json"))),
        FileMapping(
            source="claude_desktop_config.json",
            target=str(_claude_desktop / "claude_desktop_config.json"),
        ),
    ],
    packages=[
        Package(cask="claude", winget="Anthropic.Claude"),
        Package(brew="claude-code", winget="Anthropic.ClaudeCode"),
    ],
)
