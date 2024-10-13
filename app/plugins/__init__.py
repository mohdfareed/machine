"""Individual machine components setup package."""

import typer as _typer

from . import private_files

app = _typer.Typer(name="plugin", help="Machine plugins.")
app.add_typer(private_files.plugin_app)
