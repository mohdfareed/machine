"""CLI registration and the application failure boundary."""

import inspect
from collections.abc import Callable
from typing import Any

import typer

from app import cli, env, reporting
from app.cli import deploy, info, sync, upgrade
from app.validation import validate_full_disk_access

type _Callback = Callable[..., Any]


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Entry Point
# ═════════════════════════════════════════════════════════════════════════════


def main(prog_name: str | None = None) -> None:
    """Run one CLI invocation and present failures once."""
    options = cli.Options()
    try:
        _create_app()(prog_name=prog_name or cli.COMMAND, obj=options)

    # Handle user interrupts.
    except KeyboardInterrupt:
        reporting.warning("Interrupted.")
        raise SystemExit(130)

    # Present the failure with optional technical context.
    except Exception as exc:
        reporting.error(str(exc))
        if options.debug:
            reporting.exception(options.debug)
        raise SystemExit(1) from None


def _callback(
    context: typer.Context,
    debug: bool = typer.Option(
        False, "-d", "--debug", help="Show diagnostic traces and exception tracebacks."
    ),
    version: bool = typer.Option(False, "-v", "--version", help="Show version and exit."),
) -> None:
    # Keep execution options local to this invocation.
    options = context.ensure_object(cli.Options)
    options.debug = debug

    if debug:
        reporting.debug("Debug mode enabled.")
        reporting.debug(f"App: {cli.NAME} {cli.VERSION}")
        reporting.debug(f"Home: {env.ROOT}")
        reporting.debug(f"Platform: {env.PLATFORM}")

    # Handle informational exits.
    if version:
        reporting.plain(f"{cli.NAME} {cli.VERSION}")
        raise SystemExit()

    validate_full_disk_access()


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Configuration
# ═════════════════════════════════════════════════════════════════════════════


def _create_app() -> typer.Typer:
    # Create the app and attach its callback.
    app = typer.Typer(
        name=cli.COMMAND,
        help=cli.DESCRIPTION,
        no_args_is_help=True,
        invoke_without_command=True,
        context_settings=dict(
            help_option_names=["-h", "--help"],
        ),
    )
    app.callback()(_callback)

    # Register deployment commands.
    _register(app, deploy.deploy)
    _register(app, upgrade.upgrade)
    _register(app, sync.sync)
    _register(app, info.validate)

    # Group inspection commands while retaining the default configuration view.
    show = typer.Typer(invoke_without_command=True, no_args_is_help=False)
    _register(show, info.home)
    _register(show, info.machine_id, name="id")
    _register(show, info.list_mc, name="machines")
    _register(show, info.list_mod, name="modules")
    _register_group(app, info.show, show)

    return app


def _short_help(callback: _Callback) -> str:
    if short_help := inspect.getdoc(callback):
        return short_help
    raise RuntimeError(f"CLI callback {callback.__name__} needs a docstring.")


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Registration
# ═════════════════════════════════════════════════════════════════════════════


def _register(
    app: typer.Typer,
    callback: _Callback,
    *,
    panel: str | None = None,
    name: str | None = None,
) -> None:
    app.command(name, rich_help_panel=panel, short_help=_short_help(callback))(callback)


def _register_group(
    app: typer.Typer,
    callback: _Callback,
    group: typer.Typer,
    *,
    panel: str | None = None,
) -> None:
    short_help = _short_help(callback)
    group.callback(short_help=short_help)(callback)
    app.add_typer(
        group,
        name=callback.__name__,
        rich_help_panel=panel,
        short_help=short_help,
    )
