"""Individual machine components setup package."""

import inspect
from functools import partial
from types import ModuleType
from typing import Any

import typer

from app.plugins import git, private_files

app = typer.Typer(name="plugin", help="Individual plugin setup.")
app.add_typer(git.app)
app.add_typer(private_files.app)


def create(plugin: ModuleType, *partials: partial[Any]) -> typer.Typer:
    """Create a plugin from a module."""

    # Check if the module has an app
    module_app = getattr(plugin, "app", None)
    if not isinstance(module_app, typer.Typer):
        raise ValueError("Plugin does not have an app")

    # Create a new Typer app for the plugin
    plugin_app = typer.Typer(callback=module_app.callback)
    plugin_app.info = module_app.info
    plugin_app.registered_groups = module_app.registered_groups

    # Register partial functions as commands to the plugin app
    for partial_func in partials:
        plugin_app.command()(_apply_partial(partial_func))

    return plugin_app


def _apply_partial(partial_func: partial[Any]) -> Any:

    # Get the signature of the function and the arguments
    signature = inspect.signature(partial_func.func)
    args = iter(partial_func.args)
    kwargs = partial_func.keywords

    # Create the new defaults for the function
    new_defaults: list[Any] = []
    for name, param in signature.parameters.items():
        # Positional -> Keyword -> Default -> None
        new_defaults.append(next(args, kwargs.pop(name, param.default)))
        if new_defaults[-1] == inspect.Parameter.empty:
            new_defaults.pop()

    # Update the function with the new defaults
    partial_func.func.__defaults__ = tuple(new_defaults)
    return partial_func.func
