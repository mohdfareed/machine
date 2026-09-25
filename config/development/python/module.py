"""Python runtimes."""

from app.models import Module, Package

module = Module(
    packages=[
        Package(name="python", brew="python", winget="Python.Python.3.14"),
        Package(brew="python-freethreading"),
    ],
)
