"""Package managers."""

import typer as _typer

from .apt import *
from .brew import *
from .mas import *
from .package_manager import *
from .pipx import *
from .scoop import *
from .snap import *
from .winget import *

app = _typer.Typer(name="pkg", help="Package managers.")
for pkg_manager in PackageManager.available_managers():
    app.add_typer(pkg_manager.app())
