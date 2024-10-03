"""Main tests."""

from pytest import MonkeyPatch
from typer.testing import CliRunner

from app import utils
from app.main import app

runner = CliRunner()


def test_package():
    """Test the package."""

    try:
        from app import __main__ as _  # pylint: disable=import-outside-toplevel
    except SystemExit as ex:
        assert ex.code == 2


def test_app():
    """Test the app."""

    result = runner.invoke(app, ["macOS"])
    assert result.exit_code == 0
    assert "macOS" in (result.stdout.split("\n")[0])
    assert "XDG" in (result.stdout)


def test_app_windows(monkeypatch: MonkeyPatch):
    """Test the app on Windows."""

    monkeypatch.setattr(utils, "is_windows", True)
    result = runner.invoke(app, ["Windows"])
    assert result.exit_code == 0
    assert "Windows" in (result.stdout.split("\n")[0])
    assert "APPDATA" in (result.stdout)


def test_app_invalid():
    """Test the app with invalid machine."""

    result = runner.invoke(app, [""])
    assert result.exit_code != 0
    assert "No machine name provided" in result.stdout
