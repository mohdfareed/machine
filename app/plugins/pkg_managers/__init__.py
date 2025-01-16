"""Package managers."""

from inspect import isabstract as _isabstract

import typer as _typer

from app.pkg_manager import PkgManagerPlugin as _PkgManagerPlugin

from .linux import *
from .macos import *
from .misc import *
from .windows import *


def app() -> _typer.Typer:
    """Create a Typer app for the package manager plugins."""

    managers_app = _typer.Typer(name="pkg", help="Package managers.")
    for pkg_manager in _PkgManagerPlugin.__subclasses__():
        if not pkg_manager.is_supported() or _isabstract(pkg_manager):
            continue
        managers_app.add_typer(pkg_manager.manager_app())
    return managers_app
