"""Main tests."""

from pytest import MonkeyPatch
from typer.testing import CliRunner

from app import env, utils
from app.main import app

runner = CliRunner()


def test_app() -> None:
    """Test the app executing normally."""

    try:
        from app import __main__ as _  # pylint: disable=import-outside-toplevel

    except SystemExit as ex:
        assert ex.code == 2

    result = runner.invoke(app, ["test", "-h"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout.split("\n")[1]


def test_app_fail() -> None:
    """Test the app executing and failing."""

    result = runner.invoke(app, ["test", "fail"])
    assert result.exit_code == 2
    assert "Error" in result.stdout


def test_app_debug() -> None:
    """Test the app."""

    result = runner.invoke(app, ["-d", "test", "-h"])
    assert "Machine version" in result.stdout.split("\n")[0]


def test_app_unix(monkeypatch: MonkeyPatch) -> None:
    """Test the app."""

    class _PatchedPlatform:
        WINDOWS = False

    monkeypatch.setattr(utils, utils.Platform.__name__, _PatchedPlatform)
    result = runner.invoke(app, ["-d", "test", "setup"])
    assert str(env.Unix().XDG_CONFIG_HOME) in result.stdout
    assert str(env.Unix().XDG_DATA_HOME) in result.stdout


def test_app_windows(monkeypatch: MonkeyPatch) -> None:
    """Test the app on Windows."""

    class _PatchedPlatform:
        WINDOWS = True

    monkeypatch.setattr(utils, utils.Platform.__name__, _PatchedPlatform)
    result = runner.invoke(app, ["-d", "test", "setup"])
    assert str(env.Windows().APPDATA) in result.stdout
    assert str(env.Windows().LOCALAPPDATA) in result.stdout


def test_machine() -> None:
    """Test the machine CLI."""

    result = runner.invoke(app, ["test", "setup"])
    assert result.exit_code == 0


def test_pkg_manager() -> None:
    """Test the package manager CLI."""

    result = runner.invoke(app, ["test", "pkg", "test", "setup"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["test", "pkg", "test", "install", "test"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["test", "pkg", "test", "install", "test1 test2"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["test", "pkg", "test", "update"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["test", "pkg", "test", "status"])
    assert result.exit_code == 0


def test_completion_fail(monkeypatch: MonkeyPatch) -> None:
    """Test the completion CLI."""

    class _PatchedPlatform:
        UNIX = False

    monkeypatch.setattr(utils, utils.Platform.__name__, _PatchedPlatform)
    result = runner.invoke(app, ["completion", "install"])
    assert result.exit_code == 1
