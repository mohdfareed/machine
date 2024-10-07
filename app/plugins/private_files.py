"""Private files plugin."""

from pathlib import Path
from typing import Annotated

import typer

from app import config, utils

IGNORED_FIELDS = {"config"}

PrivateDirArg = Annotated[
    Path,
    typer.Argument(
        help="The private files directory.",
        callback=utils.validate(utils.is_optional, utils.is_dir),
    ),
]
PrivateConfigArg = Annotated[config.Private, utils.IgnoredArgument]
app = typer.Typer(name="private", help="Private files setup.")


@app.command()
def setup(
    private_dir: PrivateDirArg,
    private_config: Annotated[config.Private, utils.IgnoredArgument] = config.Private(),
) -> None:
    """Setup private files on a machine."""

    utils.LOGGER.info("Setting up private files...")
    machine_fields = config.Machine().model_fields.keys()
    for field in private_config.model_fields:

        if field in [*machine_fields, *IGNORED_FIELDS]:
            utils.LOGGER.debug("Skipping: %s", field)
            continue  # skip machine fields and ignored fields
        if not isinstance(path := getattr(private_config, field, None), Path):
            utils.LOGGER.debug("Skipping: %s", field)
            continue  # skip non-Path fields

        private_file = private_dir / path.name
        if not private_file.exists():
            utils.LOGGER.warning(
                "Field '%s' does not exist at: %s",
                field,
                private_file,
            )
            continue

        utils.link(private_file, path)
        utils.LOGGER.debug("Linked: %s -> %s", private_file, path)
