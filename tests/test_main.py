"""Main tests."""

from pytest import MonkeyPatch
from typer.testing import CliRunner

from app import config, utils
from app.main import app

runner = CliRunner()


def test_app() -> None:
    """Test the app executing normally."""

    try:
        from app import __main__ as _  # pylint: disable=import-outside-toplevel

    except SystemExit as ex:
        assert ex.code == 2

    result = runner.invoke(app, ["setup", "machine"])
    assert result.exit_code == 0
    assert "machine" in result.stdout.split("\n")[0]


def test_app_fail() -> None:
    """Test the app executing and failing."""

    result = runner.invoke(app, ["setup", " "])
    assert result.exit_code == 1
    assert "ERROR" in result.stdout


def test_app_debug() -> None:
    """Test the app."""

    result = runner.invoke(app, ["-d", "setup", "testing"])
    assert str(config.MachineConfig().machine) in result.stdout


def test_app_unix(monkeypatch: MonkeyPatch) -> None:
    """Test the app."""

    monkeypatch.setattr(utils, "WINDOWS", False)
    result = runner.invoke(app, ["-d", "setup", "testing"])
    assert str(config.UnixEnvironment().XDG_CONFIG_HOME) in result.stdout


def test_app_windows(monkeypatch: MonkeyPatch) -> None:
    """Test the app on Windows."""

    monkeypatch.setattr(utils, "WINDOWS", True)
    result = runner.invoke(app, ["-d", "setup", "testing"])
    assert str(config.WindowsEnvironment().APPDATA) in result.stdout
