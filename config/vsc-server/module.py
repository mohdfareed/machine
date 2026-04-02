"""VS Code Server (code serve-web) module."""

from machine.manifest import Module

# TODO: add vscode server windows support
module = Module(depends=["vscode"])
