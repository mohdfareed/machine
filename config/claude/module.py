"""Claude and Claude Code CLI configuration module."""

from pathlib import Path

from machine.core import PLATFORM, Platform
from machine.manifest import FileMapping, Module, Package

match PLATFORM:
    case Platform.WINDOWS:
        _desktop_config = Path("%APPDATA%") / "Claude"
    case Platform.MACOS:
        _desktop_config = Path("~/Library/Application Support/Claude")
    case _:  # linux
        _desktop_config = Path("~/.config/Claude")

module = Module(
    files=[
        FileMapping(
            source="claude_desktop_config.json",
            target=str(_desktop_config / "claude_desktop_config.json"),
        ),
        FileMapping(source="settings.json", target=str(Path("~/.claude/settings.json"))),
    ],
    packages=[
        Package(cask="claude", winget="Anthropic.Claude"),
        Package(brew="claude-code", winget="Anthropic.ClaudeCode"),
    ],
)
