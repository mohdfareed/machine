"""Main tests."""

from pytest import MonkeyPatch
from typer.testing import CliRunner

from app import config, utils
from app.main import app, reports

runner = CliRunner()


def test_package():
    """Test the package."""

    try:
        from app import __main__ as _  # pylint: disable=import-outside-toplevel
    except SystemExit as ex:
        assert ex.code == 2


def test_app_unix(monkeypatch: MonkeyPatch):
    """Test the app."""

    monkeypatch.setattr(utils, "WINDOWS", False)
    result = runner.invoke(app, ["macOS"])
    assert result.exit_code == 0
    assert "macOS" in (result.stdout.split("\n")[0])
    assert str(config.MachineConfig().machine) in (result.stdout)
    assert str(config.UnixEnvironment().XDG_CONFIG_HOME) in (result.stdout)


def test_app_windows(monkeypatch: MonkeyPatch):
    """Test the app on Windows."""

    monkeypatch.setattr(utils, "WINDOWS", True)
    result = runner.invoke(app, ["Windows"])
    assert result.exit_code == 0
    assert "Windows" in (result.stdout.split("\n")[0])
    assert str(config.MachineConfig().machine) in (result.stdout)
    assert str(config.WindowsEnvironment().APPDATA) in (result.stdout)


def test_app_invalid():
    """Test the app with invalid machine."""

    result = runner.invoke(app, [""])
    assert result.exit_code != 0
    assert "No machine name provided" in result.stdout


def test_setup_reports():
    """Test the setup reports."""

    reports.append("Report 1")
    reports.append("Report 2")
    result = runner.invoke(app, ["macOS"])
    assert result.exit_code == 0
    assert "Report 1" in result.stdout
    assert "Report 2" in result.stdout
