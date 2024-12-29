"""Individual machine components setup package."""

from typing import Any as _Any

import typer as _typer

from .git import *
from .nvim import *
from .plugin import *
from .powershell import *
from .private_files import *
from .python import *
from .shell import *
from .ssh import *
from .tailscale import *
from .tools import *
from .vscode import *
from .zed import *


def app(plugins: list[Plugin[_Any, _Any]]) -> _typer.Typer:
    """Create a Typer app for plugins."""

    plugins_app = _typer.Typer(name="plugin", help="Machine plugins.")
    for plugin in plugins:
        if not plugin.is_supported():
            continue
        plugins_app.add_typer(plugin.app())
    return plugins_app
