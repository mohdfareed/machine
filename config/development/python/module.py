"""Python runtimes and package tooling."""

from app.models import Module, Package, Platform

module = Module(
    packages=[
        Package(name="python", brew="python", apt="python3", winget="Python.Python.3.14"),
        Package(brew="python-freethreading"),
        Package(
            name="uv",
            brew="uv",
            winget="astral-sh.uv",
            platforms=[Platform.MACOS, Platform.WINDOWS],
        ),
        Package(
            name="uv",
            cmd="curl -LsSf https://astral.sh/uv/install.sh | sh",
            up_cmd=True,
            platforms=[Platform.LINUX, Platform.WSL],
        ),
    ],
)
