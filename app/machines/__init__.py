"""Machines setup package."""

import typer as _typer

from .machine import *
from .macos import *
from .testbench import *

app = _typer.Typer(name="machine", help="Machines setup.")

app.add_typer(Test().app())
app.add_typer(MacOS().app())
