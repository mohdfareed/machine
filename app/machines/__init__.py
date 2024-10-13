"""Machines setup package."""

import typer as _typer

from app.machines import testing

machines_app = _typer.Typer(name="machine", help="Machines setup.")
machines_app.add_typer(testing.machine_app)
