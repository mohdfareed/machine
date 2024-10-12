"""Machines setup package."""

import typer

from app.machines import testing

app = typer.Typer(name="machine", help="Machines setup.")
app.add_typer(testing.machine_app)
