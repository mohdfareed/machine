"""Machines setup package."""

import typer as _typer

from .machine import *
from .macos import *
from .testbench import *

app: _typer.Typer = _typer.Typer(name="machine", help="Machines setup.")

if Test.is_supported():
    app.add_typer(Test().app())
if MacOS.is_supported():
    app.add_typer(MacOS().app())
