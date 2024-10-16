"""Machines setup package."""

import typer as _typer

from . import macos, testbench

app = _typer.Typer(name="machine", help="Machines setup.")
app.add_typer(testbench.machine_app)
app.add_typer(macos.machine_app)
