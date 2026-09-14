"""CLI registration and the application failure boundary."""

import typer

from app import cli, reporting
from app.cli import deploy, info, sync, upgrade

# =============================================================================
# MARK: App Entry Point
# =============================================================================


def main(prog_name: str | None = None) -> None:
    """Run one CLI invocation and present failures once."""
    options = cli.Options()
    try:
        _create_app()(prog_name=prog_name or cli.COMMAND, obj=options)

    # Handle user interrupts.
    except KeyboardInterrupt:
        reporting.error("Interrupted.")
        raise SystemExit(130)

    # Present the failure with optional technical context.
    except Exception as exc:
        reporting.error(str(exc))
        if options.debug:
            reporting.exception()
            raise SystemExit(1)

        reporting.detail("Run with --debug for details.", error=True)
        raise SystemExit(1)


# =============================================================================
# MARK: App Configuration
# =============================================================================


def _callback(
    context: typer.Context,
    debug: bool = typer.Option(False, "-d", "--debug", help="Show exception tracebacks."),
    version: bool = typer.Option(False, "-v", "--version", help="Show version and exit."),
) -> None:
    # Keep execution options local to this invocation.
    options = context.ensure_object(cli.Options)
    options.debug = debug

    # Handle informational exits.
    if version:
        reporting.plain(f"{cli.NAME} {cli.VERSION}")
        raise typer.Exit()


def _create_app() -> typer.Typer:
    # Create the app and attach its callback.
    app = typer.Typer(
        name=cli.COMMAND,
        help=cli.DESCRIPTION,
        no_args_is_help=True,
        invoke_without_command=True,
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    app.callback()(_callback)

    # Register deployment commands.
    app.command(rich_help_panel="Deployment")(deploy.deploy)
    app.command(rich_help_panel="Deployment")(upgrade.upgrade)
    app.command(rich_help_panel="Deployment")(sync.sync)

    # Group inspection commands while retaining the default configuration view.
    show = typer.Typer(invoke_without_command=True, no_args_is_help=False)
    show.callback()(info.show)
    show.command("id")(info.machine_id)
    show.command()(info.home)
    show.command()(info.private)
    show.command()(info.status)
    app.add_typer(show, name=info.show.__name__, rich_help_panel="Info")
    app.command("list", rich_help_panel="Info")(info.list_all)
    return app
