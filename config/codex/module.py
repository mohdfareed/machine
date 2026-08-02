"""OpenAI Codex and ChatGPT configuration module."""

from machine.manifest import FileMapping, Module, Package

module = Module(
    packages=[
        Package(name="codex", cask="codex", winget="OpenAI.Codex"),
        Package(name="chatgpt", cask="chatgpt", winget="9PLM9XGG6VKS"),
    ],
)
