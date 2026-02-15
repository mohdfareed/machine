"""Enable `python -m machine`."""

from machine.cli import main
from machine.config import app_settings

if __name__ == "__main__":
    main(prog_name=app_settings.name)
