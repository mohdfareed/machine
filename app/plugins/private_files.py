"""Private files plugin."""

from pathlib import Path
from typing import Annotated

import typer

from app import config, utils

PrivateDirArg = Annotated[
    Path,
    typer.Option(
        prompt=True,
        help="The private files directory.",
        callback=utils.validate(utils.is_dir),
    ),
]
PrivateConfigArg = Annotated[config.Private, utils.InternalArg]
app = typer.Typer(name="git", help="Configure git.")


@app.command()
def setup(
    private_dir: PrivateDirArg,
    private_config: PrivateConfigArg = config.Private(),
) -> None:
    """Setup private files on a machine."""
    utils.LOGGER.info("Setting up private files...")
    utils.LOGGER.debug("Private directory: %s", private_dir)

    machine_fields = config.Machine().model_fields.keys()
    ignored_fields = [*machine_fields, *private_config.excluded_fields]

    for field, info in private_config.model_fields.items():
        if (info.annotation is not Path) or (field in ignored_fields):
            continue  # skip ignored and non-Path fields

        path: Path = getattr(private_config, field)
        private_file = private_dir / path.name
        if not private_file.exists():
            utils.LOGGER.warning(
                "Private field '%s' does not exist at: %s", field, private_file
            )
            continue

        utils.link(private_file, path)
        utils.LOGGER.debug("Linked: %s -> %s", private_file, path)
