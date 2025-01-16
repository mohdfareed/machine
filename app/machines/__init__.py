"""Machines setup package."""

from inspect import isabstract as _isabstract
from typing import Any as _Any

import typer as _typer

from app.machine import MachinePlugin as _MachinePlugin

from .codespaces import *
from .gleason import *
from .macos import *
from .rpi import *
from .testbench import *
from .windows import *


def apps() -> list[_typer.Typer]:
    """List of supported machines apps."""
    machine: _MachinePlugin[_Any, _Any]
    machines: list[_typer.Typer] = []

    for machine in _MachinePlugin.__subclasses__():  # type: ignore
        if not machine.is_supported() or _isabstract(machine):
            continue
        machines.append(machine.machine_app())
    return machines
