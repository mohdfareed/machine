"""Chat agents configuration module."""

from app.models import FileMapping, Module, Package

module = Module(
    files=[
        FileMapping(source="AGENTS.md", target="~/.codex/AGENTS.md"),
        FileMapping(source="skills", target="~/.agents/skills"),
    ],
    packages=[Package(name="codex", cask="codex", winget="OpenAI.Codex")],
)
