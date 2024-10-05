"""Private files plugin."""

from pathlib import Path
from typing import Annotated

import typer

from app import config, utils

IGNORED_FIELDS = {"config"}

app = typer.Typer(name="private", help="Private files setup.")


@app.command()
def setup(
    private_dir: Annotated[
        Path,
        typer.Argument(
            help="The private files directory.",
            callback=utils.validate(utils.path_exists, utils.is_dir),
        ),
    ],
    private_config: Annotated[
        config.Private,
        utils.IgnoredArgument,
    ] = config.Private(),
) -> None:
    """Setup private files on a machine."""

    utils.LOGGER.info("Setting up private files...")
    machine_fields = config.Machine().model_fields.keys()
    for field in private_config.model_fields:
        utils.LOGGER.debug("Skipping: %s", field)
        if field in [*machine_fields, *IGNORED_FIELDS]:
            continue
        if not isinstance(path := getattr(private_config, field), Path):
            continue

        private_file = private_dir / path.name
        if not private_file.exists():
            utils.LOGGER.warning("Private file does not exist: %s", private_file)
            continue

        utils.link(private_file, path)
        utils.LOGGER.debug("Linked: %s -> %s", private_file, path)
    utils.LOGGER.debug("Private files setup complete")
