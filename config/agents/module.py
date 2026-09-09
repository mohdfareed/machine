"""Chat agents configuration module."""

from app.models import Module, Package

module = Module(
    packages=[Package(name="codex", cask="codex", winget="OpenAI.Codex")],
)
