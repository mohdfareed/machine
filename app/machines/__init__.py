"""Machines setup package."""

import typer as _typer

from . import testing

app = _typer.Typer(name="machine", help="Machines setup.")
app.add_typer(testing.machine_app)
