"""Main tests."""

from typer.testing import CliRunner

from app.main import app

runner = CliRunner()


def test_app():
    """Test the Typer app."""

    result = runner.invoke(app, ["macOS"])
    assert result.exit_code == 0
    assert "Setting up macOS..." in result.stdout
    assert "Done!" in result.stdout
