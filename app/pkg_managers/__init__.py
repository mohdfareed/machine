"""Package managers."""

import typer as _typer

from .linux import *
from .macos import *
from .misc import *
from .pkg_manager import *
from .windows import *

app = _typer.Typer(name="pkg", help="Package managers.")

for pkg_manager in PkgManager.__subclasses__():
    if not pkg_manager.is_supported():
        continue
    app.add_typer(pkg_manager().app())
