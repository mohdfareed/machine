"""Machines setup package."""

import typer as _typer

from .macos import *
from .testbench import *

apps: list["_typer.Typer"] = []
if MacOS.is_supported():
    apps.append(MacOS.machine_app(MacOS()))
if Test.is_supported():
    apps.append(Test.machine_app(Test()))
