"""OpenAI Codex and ChatGPT configuration module."""

from app.machine import FileMapping, Module, Package

module = Module(
    packages=[Package(name="codex", cask="codex", winget="OpenAI.Codex")],
)
